"""Shioaji 券商封裝層。

把所有「跟永豐主機講話」的動作集中在這裡：登入、啟用憑證、解析契約、
下單、撤單、查部位。其餘模組只跟本類別互動，不直接碰 shioaji。

支援三層安全：
  1. DRY_RUN  : 不送單，只記 log（回傳假的 trade 物件）。
  2. SIMULATION: 送到永豐模擬主機（假錢）。
  3. LIVE     : 真錢，需 CA + 最終確認鎖。
"""
from __future__ import annotations

import logging
from typing import Callable, List, Optional

try:
    import shioaji as sj
    from shioaji.constant import (
        Action,
        FuturesOCType,
        FuturesPriceType,
        OrderType,
        QuoteType,
    )
    _SHIOAJI_AVAILABLE = True
except Exception:  # pragma: no cover - 套件未安裝時仍可載入做語法/單測
    sj = None
    Action = FuturesOCType = FuturesPriceType = OrderType = QuoteType = None
    _SHIOAJI_AVAILABLE = False

from .config import Config


class _FakeTrade:
    """DRY_RUN 用的假成交單，介面盡量貼近 shioaji.Trade。"""

    def __init__(self, action: str, price: float, qty: int):
        self.fake = True
        self.action = action
        self.price = price
        self.quantity = qty


class Broker:
    def __init__(self, cfg: Config, logger: logging.Logger):
        self.cfg = cfg
        self.log = logger
        self.api = None
        self.signal_contract = None   # TXF（近月連續）
        self.order_contract = None    # TMF/MXF 當月
        self._connected = False

    # ------------------------------------------------------------------ #
    #  登入 / 初始化
    # ------------------------------------------------------------------ #
    def connect(self) -> None:
        if self.cfg.dry_run:
            self.log.warning("【DRY_RUN】不連線主機，僅模擬訊號與下單流程。")
        if not _SHIOAJI_AVAILABLE:
            if self.cfg.dry_run:
                self.log.warning("shioaji 未安裝，DRY_RUN 下仍可跑流程但無真實報價。")
                return
            raise RuntimeError("未安裝 shioaji 套件，無法連線。請 pip install shioaji。")

        self.log.info(
            "登入 Shioaji（simulation=%s, dry_run=%s, live=%s）",
            self.cfg.simulation, self.cfg.dry_run, self.cfg.is_live,
        )
        self.api = sj.Shioaji(simulation=self.cfg.simulation)
        self.api.login(
            api_key=self.cfg.api_key,
            secret_key=self.cfg.secret_key,
            fetch_contract=True,
            contracts_timeout=10_000,
        )
        self._connected = True
        self.log.info("登入成功。")

        # 啟用憑證：實單必需；模擬主機通常不需要，但有設就啟用。
        if self.cfg.ca_path and self.cfg.ca_passwd and self.cfg.person_id:
            try:
                ok = self.api.activate_ca(
                    ca_path=self.cfg.ca_path,
                    ca_passwd=self.cfg.ca_passwd,
                    person_id=self.cfg.person_id,
                )
                self.log.info("啟用憑證 CA: %s", ok)
            except Exception as e:  # noqa: BLE001
                self.log.error("啟用憑證失敗: %s", e)
                if self.cfg.is_live:
                    raise

        self._resolve_contracts()

    def _resolve_contracts(self) -> None:
        """解析訊號契約（TXF 近月連續）與下單契約（當月）。"""
        # 訊號：用 R1 近月連續，報價最連貫。
        sig = self.cfg.signal_symbol
        self.signal_contract = getattr(self.api.Contracts.Futures, sig)[f"{sig}R1"]

        # 下單：取「當月」契約（成交量最大、流動性最好）。
        self.order_contract = self._front_month(self.cfg.order_symbol)

        self.log.info(
            "訊號契約=%s(%s)  下單契約=%s(%s)",
            self.signal_contract.code, self.cfg.signal_spec.name_zh,
            self.order_contract.code, self.cfg.order_spec.name_zh,
        )

    def _front_month(self, symbol: str):
        """挑出當月（最近到期、非 R1/R2 連續代碼）契約。"""
        cat = getattr(self.api.Contracts.Futures, symbol)
        candidates = [
            c for c in cat
            if not c.code.endswith("R1") and not c.code.endswith("R2")
            and c.delivery_month  # 有交割月
        ]
        if not candidates:
            # 退而求其次用近月連續。
            return cat[f"{symbol}R1"]
        candidates.sort(key=lambda c: c.delivery_month)
        return candidates[0]

    # ------------------------------------------------------------------ #
    #  報價訂閱
    # ------------------------------------------------------------------ #
    def subscribe_signal(self) -> None:
        """訂閱 TXF 的 Tick 與 BidAsk。"""
        if self.cfg.dry_run and not self._connected:
            self.log.warning("【DRY_RUN】跳過真實報價訂閱。")
            return
        self.api.quote.subscribe(self.signal_contract, quote_type=QuoteType.Tick, version="v1")
        self.api.quote.subscribe(self.signal_contract, quote_type=QuoteType.BidAsk, version="v1")
        self.log.info("已訂閱 %s 的 Tick 與 BidAsk。", self.signal_contract.code)

    def subscribe_order_contract(self) -> None:
        """訂閱下單契約的 Tick，用於即時估算未實現損益與停損。"""
        if self.cfg.dry_run and not self._connected:
            return
        self.api.quote.subscribe(self.order_contract, quote_type=QuoteType.Tick, version="v1")
        self.log.info("已訂閱下單契約 %s 的 Tick（估損益用）。", self.order_contract.code)

    def set_callbacks(
        self,
        on_signal_tick: Callable,
        on_signal_bidask: Callable,
        on_order_tick: Callable,
        on_order_status: Callable,
    ) -> None:
        """註冊報價與委託回報 callback。"""
        if not self._connected:
            return

        sig_code = self.signal_contract.code
        ord_code = self.order_contract.code

        @self.api.on_tick_fop_v1()
        def _tick(exchange, tick):  # noqa: ANN001
            if tick.code == sig_code:
                on_signal_tick(tick)
            elif tick.code == ord_code:
                on_order_tick(tick)

        @self.api.on_bidask_fop_v1()
        def _bidask(exchange, bidask):  # noqa: ANN001
            if bidask.code == sig_code:
                on_signal_bidask(bidask)

        self.api.set_order_callback(on_order_status)
        self.log.info("已註冊報價與委託回報 callback。")

    # ------------------------------------------------------------------ #
    #  下單 / 撤單
    # ------------------------------------------------------------------ #
    def place_market(self, action: str, qty: int, range_market: bool = True, reason: str = ""):
        """對下單契約送出（範圍）市價單。

        action: "Buy" / "Sell"
        range_market=True 用範圍市價(MKP)，False 用市價(MKT)。
        當沖一律 IOC，避免掛單殘留。
        """
        self.log.info(
            "下單請求: %s %d 口 %s (%s) 原因=%s",
            action, qty, self.cfg.order_symbol,
            "範圍市價" if range_market else "市價", reason,
        )

        if self.cfg.dry_run:
            self.log.warning("【DRY_RUN】不真的送單。")
            return _FakeTrade(action, self.order_contract_price(), qty)

        price_type = FuturesPriceType.MKP if range_market else FuturesPriceType.MKT
        order = self.api.Order(
            action=Action.Buy if action == "Buy" else Action.Sell,
            price=0,
            quantity=qty,
            price_type=price_type,
            order_type=OrderType.IOC,
            octype=FuturesOCType.Auto,
            account=self.api.futopt_account,
        )
        trade = self.api.place_order(self.order_contract, order)
        self.log.info("已送單: %s", getattr(trade, "status", trade))
        return trade

    def cancel_all(self) -> None:
        """撤銷所有未成交委託。"""
        if self.cfg.dry_run or not self._connected:
            self.log.warning("【DRY_RUN/未連線】略過撤單。")
            return
        try:
            self.api.update_status(self.api.futopt_account)
            for trade in self.api.list_trades():
                status = getattr(trade.status, "status", None)
                # 只撤仍可能成交的單。
                if str(status) in ("Submitted", "PreSubmitted", "PartFilled", "PendingSubmit"):
                    try:
                        self.api.cancel_order(trade)
                        self.log.info("已撤單: %s", trade.order.id)
                    except Exception as e:  # noqa: BLE001
                        self.log.error("撤單失敗 %s: %s", trade.order.id, e)
        except Exception as e:  # noqa: BLE001
            self.log.error("撤單流程錯誤: %s", e)

    # ------------------------------------------------------------------ #
    #  查詢
    # ------------------------------------------------------------------ #
    def get_net_position(self) -> tuple[int, float]:
        """回傳主機端淨部位 (口數帶正負, 均價)。查不到回 (0, 0)。"""
        if self.cfg.dry_run or not self._connected:
            return 0, 0.0
        try:
            positions = self.api.list_positions(self.api.futopt_account)
            net, cost_qty = 0, 0.0
            for p in positions:
                if p.code != self.order_contract.code:
                    continue
                signed = p.quantity if str(p.direction) in ("Action.Buy", "Buy") else -p.quantity
                net += signed
                cost_qty += p.price * abs(signed)
            avg = (cost_qty / abs(net)) if net else 0.0
            return net, avg
        except Exception as e:  # noqa: BLE001
            self.log.error("查詢部位失敗: %s", e)
            return 0, 0.0

    def list_open_positions(self) -> List:
        if self.cfg.dry_run or not self._connected:
            return []
        try:
            return self.api.list_positions(self.api.futopt_account)
        except Exception as e:  # noqa: BLE001
            self.log.error("查詢部位失敗: %s", e)
            return []

    def order_contract_price(self) -> float:
        """取得下單契約參考價（DRY_RUN 估損益用，無真實報價時回 0）。"""
        return 0.0

    # ------------------------------------------------------------------ #
    def logout(self) -> None:
        if self._connected and self.api is not None:
            try:
                self.api.logout()
                self.log.info("已登出 Shioaji。")
            except Exception as e:  # noqa: BLE001
                self.log.error("登出錯誤: %s", e)
