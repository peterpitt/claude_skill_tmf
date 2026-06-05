"""主協調器：把報價、訊號、下單、時段、風控全部串起來。

執行緒模型：
  - 主執行緒：建立連線、註冊 callback，然後進入監看迴圈（印狀態、處理換日/收盤）。
  - Shioaji callback 執行緒：報價/委託回報進來時驅動訊號與部位更新。
  - 風控執行緒：獨立監控損益，必要時斷路。

所有「會送單」的進入點都先過三道閘：
  風控未觸發 → 時段可進場 → 出手次數未滿。
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Optional

from .broker import Broker
from .config import Config
from .kbar import KBarAggregator
from .market_data import FVDTracker
from .position_book import PositionBook
from .risk import CircuitBreaker
from .session import SessionManager, SessionType
from .strategy import Signal, Strategy
from .strategy_orb import ORBStrategy, Signal as ORBSignal


class Trader:
    def __init__(self, cfg: Config, logger: logging.Logger):
        self.cfg = cfg
        self.log = logger

        self.book = PositionBook(cfg.order_spec.point_value)
        self.broker = Broker(cfg, logger)
        self.agg = KBarAggregator(cfg.kbar_minutes, cfg.ma_period)
        self.fvd = FVDTracker(cfg.fvd_window_seconds)
        self.session = SessionManager(cfg)
        # 策略選擇：ORB（完全 bar-based，可用 K 線回測）或舊版 MA+FVD。
        if cfg.strategy == "orb":
            self.orb = ORBStrategy(cfg, self.session, logger)
            self.strategy = None
        else:
            self.orb = None
            self.strategy = Strategy(cfg, self.agg, self.fvd, logger)
        # ORB 動態出場狀態（進場時設定）
        self._orb_dir = 0
        self._orb_entry = 0.0
        self._orb_stop = 0.0
        self._orb_target = 0.0
        self._orb_risk = 0.0
        self._orb_best = 0.0
        self.risk = CircuitBreaker(
            cfg, self.book,
            flatten_all=self.flatten_all,
            cancel_all=self.broker.cancel_all,
            logger=logger,
            get_price=lambda: self.book.last_price,
        )

        self._order_lock = threading.Lock()   # 序列化下單，避免重複/競態
        self._stop = threading.Event()
        self._forced_closed_session: Optional[tuple] = None  # 已強制平倉的時段

    # ------------------------------------------------------------------ #
    #  啟動 / 關閉
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        self._banner()
        self.broker.connect()
        self.broker.subscribe_signal()
        self.broker.subscribe_order_contract()
        self.broker.set_callbacks(
            on_signal_tick=self.on_signal_tick,
            on_signal_bidask=self.on_signal_bidask,
            on_order_tick=self.on_order_tick,
            on_order_status=self.on_order_status,
        )
        self.risk.start()
        self.log.info("系統啟動完成，進入監看迴圈。Ctrl-C 可安全停止。")
        self._supervise()

    def stop(self) -> None:
        self._stop.set()

    def shutdown(self) -> None:
        self.log.info("正在安全關閉…")
        self.risk.stop()
        # 收手前確保不留倉。
        if self.book.position != 0:
            self.log.warning("關閉前仍有部位，市價平倉。")
            self.flatten_all("SHUTDOWN")
        self.broker.cancel_all()
        self.broker.logout()
        self.log.info("已安全關閉。今日損益快照：%s", self.book.snapshot())

    # ------------------------------------------------------------------ #
    #  監看迴圈（主執行緒）
    # ------------------------------------------------------------------ #
    def _supervise(self) -> None:
        import time as _t
        last_status = 0.0
        try:
            while not self._stop.is_set():
                now = self.session.now()
                self._handle_force_close(now)
                # 每 30 秒印一次狀態心跳。
                if _t.time() - last_status >= 30:
                    self._heartbeat(now)
                    last_status = _t.time()
                _t.sleep(1.0)
        except KeyboardInterrupt:
            self.log.info("收到中斷訊號。")
        finally:
            self.shutdown()

    def _handle_force_close(self, now: datetime) -> None:
        """收盤前 15 分鐘強制平倉，且整段窗內維持平倉、停新倉。"""
        if not self.session.in_force_close_window(now):
            return
        sess_key = (self.session._trading_day_key(now), self.session.current_session(now))
        if self._forced_closed_session == sess_key:
            return  # 本時段已處理過
        if self.book.position != 0:
            self.log.warning("【收盤前強制平倉】時段=%s 平掉所有部位。", sess_key[1].value)
            self.flatten_all("FORCE_CLOSE")
        self.broker.cancel_all()
        self._forced_closed_session = sess_key

    def _heartbeat(self, now: datetime) -> None:
        sess = self.session.current_session(now)
        self.log.info(
            "[心跳] %s 時段=%s 可進場=%s 出手=%d/%d MA備齊=%s FVD=%+d 部位=%d 損益=%s 斷路=%s",
            now.strftime("%H:%M:%S"), sess.value, self.session.can_enter(now),
            self.session.entries_used(now), self.cfg.max_entries_per_session,
            self.agg.ready(), self.fvd.fvd(), self.book.position,
            self.book.snapshot()["total"], self.risk.tripped,
        )

    # ------------------------------------------------------------------ #
    #  報價 callback
    # ------------------------------------------------------------------ #
    def on_signal_tick(self, tick) -> None:  # noqa: ANN001
        """TXF 逐筆 → 餵 K 棒 + FVD；跨棒時評估訊號。"""
        try:
            ts = self._tick_dt(tick)
            price = float(tick.close)
            vol = int(getattr(tick, "volume", 0) or 0)
            ttype = int(getattr(tick, "tick_type", 0) or 0)

            self.fvd.add_tick(ts, vol, ttype)
            closed = self.agg.add_tick(ts, price, vol)
            if closed is not None:
                self._on_bar_close(closed, ts)
        except Exception as e:  # noqa: BLE001
            self.log.error("處理 TXF tick 失敗: %s", e)

    def on_signal_bidask(self, bidask) -> None:  # noqa: ANN001
        try:
            bid = sum(int(x) for x in getattr(bidask, "bid_volume", []) or [])
            ask = sum(int(x) for x in getattr(bidask, "ask_volume", []) or [])
            self.fvd.add_bidask(bid, ask)
        except Exception as e:  # noqa: BLE001
            self.log.debug("處理 BidAsk 失敗: %s", e)

    def on_order_tick(self, tick) -> None:  # noqa: ANN001
        """下單契約逐筆 → 更新最新價，供未實現損益/停損估算。"""
        try:
            price = float(tick.close)
            self.book.update_last_price(price)
            self._check_per_trade_stop(price)
        except Exception as e:  # noqa: BLE001
            self.log.debug("處理下單契約 tick 失敗: %s", e)

    def on_order_status(self, state, msg) -> None:  # noqa: ANN001
        """委託/成交回報。只在『成交』時更新部位簿。"""
        try:
            self.log.info("委託回報: state=%s msg=%s", state, msg)
            # Shioaji 成交回報 (FDeal) 會帶 action/price/quantity。
            if isinstance(msg, dict):
                deal = msg
            else:
                deal = getattr(msg, "__dict__", {})
            action = str(deal.get("action", "")).replace("Action.", "")
            price = deal.get("price")
            qty = deal.get("quantity")
            code = deal.get("code")
            # 僅處理本下單契約的成交。
            if (
                action in ("Buy", "Sell")
                and price and qty
                and (code is None or code == self.broker.order_contract.code)
                and self._is_deal(state)
            ):
                self.book.on_fill(action, float(price), int(qty))
                self.log.info("成交更新部位簿: %s", self.book.snapshot())
        except Exception as e:  # noqa: BLE001
            self.log.error("處理委託回報失敗: %s", e)

    @staticmethod
    def _is_deal(state) -> bool:
        s = str(state)
        return "Deal" in s or "Filled" in s or "FDeal" in s

    # ------------------------------------------------------------------ #
    #  訊號 → 下單
    # ------------------------------------------------------------------ #
    def _on_bar_close(self, closed, now=None) -> None:
        self.log.info("%d分K收盤: %s", self.cfg.kbar_minutes, closed)
        if self.orb is not None:
            self._on_bar_close_orb(closed, now)
            return

        signal = self.strategy.on_bar_close(closed, self.book.position, now)
        if signal == Signal.NONE:
            return

        if signal == Signal.EXIT:
            if self.book.position != 0:
                self.log.info("均線反向 → 出場。")
                self.flatten_all("MA_REVERSE")
            return

        # 進場訊號：過三道閘。
        if signal in (Signal.ENTER_LONG, Signal.ENTER_SHORT):
            self._try_enter(signal)

    def _on_bar_close_orb(self, closed, now) -> None:
        """ORB 策略：bar 收盤決策（反向突破出場 / 開盤區間突破進場）。"""
        now = now or self.session.now()
        dec = self.orb.on_bar(closed, self.book.position, now)
        if dec.signal == ORBSignal.EXIT and self.book.position != 0:
            self.log.info("ORB 反向突破 → 出場（%s）。", dec.reason)
            self.flatten_all("ORB_REVERSE")
            return
        if dec.signal in (ORBSignal.ENTER_LONG, ORBSignal.ENTER_SHORT):
            sig = Signal.ENTER_LONG if dec.signal == ORBSignal.ENTER_LONG else Signal.ENTER_SHORT
            if self._try_enter(sig):
                # 進場成功 → 記錄動態停損/停利。
                self._orb_dir = 1 if sig == Signal.ENTER_LONG else -1
                entry = self.book.last_price or closed.close
                self._orb_entry = entry
                self._orb_stop = dec.stop_price if dec.stop_price else (
                    entry - self._orb_dir * self.cfg.per_trade_stop_points)
                self._orb_risk = abs(entry - self._orb_stop)
                if self.cfg.orb_take_profit_R > 0 and self._orb_risk > 0:
                    self._orb_target = entry + self._orb_dir * self._orb_risk * self.cfg.orb_take_profit_R
                else:
                    self._orb_target = 0.0
                self._orb_best = entry
                self.log.info("ORB 進場 dir=%d entry≈%.0f 停損=%.0f 停利=%.0f",
                              self._orb_dir, entry, self._orb_stop, self._orb_target)

    def _try_enter(self, signal: Signal) -> bool:
        now = self.session.now()
        if self.risk.tripped:
            self.log.warning("斷路器已觸發，今日禁止進場。")
            return False
        if not self.session.can_enter(now):
            self.log.info(
                "不進場：時段可進場=%s 出手=%d/%d",
                self.session.is_tradable(now),
                self.session.entries_used(now), self.cfg.max_entries_per_session,
            )
            return False
        if self.book.position != 0:
            self.log.info("已有部位，不重複進場。")
            return False

        with self._order_lock:
            # double-check（鎖內再確認，防止 callback 競態）。
            if self.book.position != 0 or self.risk.tripped or not self.session.can_enter(now):
                return False
            action = "Buy" if signal == Signal.ENTER_LONG else "Sell"
            self.broker.place_market(action, self.cfg.order_quantity, range_market=True,
                                     reason=f"ENTRY_{signal.name}")
            n = self.session.record_entry(now)
            self.log.info("本時段第 %d/%d 次進場（%s）。",
                          n, self.cfg.max_entries_per_session, action)
            return True

    def _check_per_trade_stop(self, price: float) -> None:
        """單筆出場：ORB 用動態停損/停利/移動停損；MA 版用固定點數停損。"""
        if self.book.position == 0:
            return
        if self.orb is not None:
            self._check_orb_exit(price)
            return
        loss_twd = self.book.unrealized_pnl_twd(price)
        if loss_twd <= -self.cfg.per_trade_stop_twd():
            self.log.warning(
                "【單筆停損】未實現損益 %.0f TWD ≤ -%.0f，市價平倉。",
                loss_twd, self.cfg.per_trade_stop_twd(),
            )
            self.flatten_all("PER_TRADE_STOP")

    def _check_orb_exit(self, price: float) -> None:
        """ORB 即時出場：停損、停利、達 1R 後移動停損鎖獲利。"""
        d = self._orb_dir
        if d == 0 or price <= 0:
            return
        # 移動停損：價格朝有利方向走，達 1R 後以「最佳價 ∓ 1R」追蹤鎖獲利。
        if self.cfg.orb_use_trailing and self._orb_risk > 0:
            if d > 0:
                self._orb_best = max(self._orb_best, price)
                if self._orb_best - self._orb_entry >= self._orb_risk:
                    self._orb_stop = max(self._orb_stop, self._orb_best - self._orb_risk)
            else:
                self._orb_best = min(self._orb_best, price)
                if self._orb_entry - self._orb_best >= self._orb_risk:
                    self._orb_stop = min(self._orb_stop, self._orb_best + self._orb_risk)
        hit_stop = (d > 0 and price <= self._orb_stop) or (d < 0 and price >= self._orb_stop)
        hit_tgt = self._orb_target > 0 and (
            (d > 0 and price >= self._orb_target) or (d < 0 and price <= self._orb_target))
        if hit_stop:
            self.log.warning("【ORB 停損】價 %.0f 觸及停損 %.0f，平倉。", price, self._orb_stop)
            self._orb_dir = 0
            self.flatten_all("ORB_STOP")
        elif hit_tgt:
            self.log.info("【ORB 停利】價 %.0f 觸及停利 %.0f，平倉。", price, self._orb_target)
            self._orb_dir = 0
            self.flatten_all("ORB_TARGET")

    # ------------------------------------------------------------------ #
    #  平倉
    # ------------------------------------------------------------------ #
    def flatten_all(self, reason: str) -> None:
        """市價平掉所有部位（被風控、停損、收盤、關閉等共用）。"""
        with self._order_lock:
            self._orb_dir = 0  # 清掉 ORB 動態出場狀態，避免殘留停損誤觸
            pos = self.book.position
            if pos == 0:
                return
            action = "Sell" if pos > 0 else "Buy"
            qty = abs(pos)
            self.log.warning("平倉 %s %d 口（原因=%s）。", action, qty, reason)
            # 平倉用一般市價(MKT)求即時成交，不用範圍市價，確保出得掉。
            self.broker.place_market(action, qty, range_market=False, reason=f"FLATTEN_{reason}")
            # DRY_RUN 下沒有真實成交回報，手動把部位歸零以維持簿一致。
            if self.cfg.dry_run:
                self.book.on_fill(action, self.book.last_price or self.book.avg_price, qty)

    # ------------------------------------------------------------------ #
    def _tick_dt(self, tick) -> datetime:
        from .config import TZ
        dt = getattr(tick, "datetime", None)
        if isinstance(dt, datetime):
            return dt if dt.tzinfo else TZ.localize(dt)
        return datetime.now(TZ)

    def _banner(self) -> None:
        c = self.cfg
        mode = "真錢實單 🔴" if c.is_live else ("模擬主機 🟡" if not c.dry_run else "DRY_RUN 🟢")
        self.log.info("=" * 64)
        self.log.info(" TMF/MXF 台指期自動當沖系統 v1")
        self.log.info(" 模式            : %s", mode)
        self.log.info(" 訊號契約        : %s (%s)", c.signal_symbol, c.signal_spec.name_zh)
        self.log.info(" 下單契約        : %s (%s, %d 元/點) x %d 口",
                      c.order_symbol, c.order_spec.name_zh,
                      c.order_spec.point_value, c.order_quantity)
        self.log.info(" 本金            : %d TWD", c.account_capital_twd)
        if c.strategy == "orb":
            self.log.info(" 策略            : ORB 開盤區間突破 %d分K OR%d分 buf%.0f VWAP=%s TP%.1fR trail=%s",
                          c.kbar_minutes, c.or_minutes, c.orb_breakout_buffer_points,
                          c.orb_use_vwap_filter, c.orb_take_profit_R, c.orb_use_trailing)
        else:
            self.log.info(" 策略            : %d分K %dMA + FVD(±%d/%ds)",
                          c.kbar_minutes, c.ma_period, c.fvd_entry_threshold, c.fvd_window_seconds)
        self.log.info(" 單筆停損        : %.0f 點 (≈%.0f TWD)",
                      c.per_trade_stop_points, c.per_trade_stop_twd())
        self.log.info(" 當日斷路器      : 累計虧損 %.0f TWD", c.daily_max_loss_twd)
        self.log.info(" 出手上限        : 早/夜盤各 %d 次", c.max_entries_per_session)
        self.log.info(" 收盤前強制平倉  : %d 分鐘", c.force_close_minutes_before)
        self.log.info("=" * 64)
