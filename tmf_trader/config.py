"""全域設定。

所有「會影響真錢」的數字都集中在這裡，方便審查與單元測試。
請把這個檔案當成保險絲盒：每一個值都先想清楚最壞情況再改。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import time
from typing import Dict

import pytz

# --------------------------------------------------------------------------- #
#  時區：台灣期交所一律使用 Asia/Taipei，永遠不要用系統 local time 直接比較。
# --------------------------------------------------------------------------- #
TZ = pytz.timezone("Asia/Taipei")


# --------------------------------------------------------------------------- #
#  契約規格
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ContractSpec:
    """單一期貨契約的規格。"""

    symbol: str           # Shioaji Contracts.Futures 底下的代碼，如 "TMF" / "MXF" / "TXF"
    name_zh: str          # 中文名
    point_value: int      # 每 1 點 = 多少 TWD
    tick_size: float = 1.0  # 最小跳動點 (台指期為 1 點)


# TAIFEX 三種台指期規格。注意「微型 != 小型」，每點價值差 5 倍。
CONTRACT_SPECS: Dict[str, ContractSpec] = {
    "TXF": ContractSpec("TXF", "臺股期貨(大台)", 200),
    "MXF": ContractSpec("MXF", "小型臺指(小台)", 50),
    "TMF": ContractSpec("TMF", "微型臺指(微台)", 10),
}


@dataclass
class Config:
    """系統設定。預設值已盡量保守，實單前務必逐項確認。"""

    # ---- 訊號來源契約：訂閱「大台 TXF」算訊號 ---------------------------- #
    signal_symbol: str = "TXF"

    # ---- 實際下單契約 -------------------------------------------------- #
    #  prompt 寫「微型台指期 (MXF)」，但 TAIFEX 上：
    #     MXF = 小型臺指 (NT$50/點)，TMF = 微型臺指 (NT$10/點)。
    #  repo 名稱為 tmf 且明確寫「微型」，故預設用真正的微型 TMF（部位風險最小）。
    #  若你確定要下小台，把這裡改成 "MXF" 即可，風控數字會自動換算。
    order_symbol: str = "TMF"

    # ---- 每次下單口數 -------------------------------------------------- #
    order_quantity: int = 1

    # ---- 帳戶本金（僅供記錄與部位上限檢查）---------------------------- #
    account_capital_twd: int = 70_000

    # ---- K 線 / 均線 --------------------------------------------------- #
    kbar_minutes: int = 5     # 5 分 K
    ma_period: int = 21       # 21MA

    # ---- FVD（內外盤委託動能）---------------------------------------- #
    #  以最近 N 秒的「外盤成交量 - 內盤成交量」累積值作為動能。
    fvd_window_seconds: int = 60
    #  進場要求 FVD 與均線方向一致，且絕對值需 >= 此門檻（口/張）。
    fvd_entry_threshold: int = 30

    # ---- 趨勢品質濾網（降低盤整假突破的洗損）------------------------- #
    #  收盤需『站穩』均線：突破幅度至少這麼多點才算數（0=不啟用）。
    entry_ma_buffer_points: float = 3.0
    #  只順著均線斜率方向進場：多單要 MA 上揚、空單要 MA 下彎。
    use_ma_slope_filter: bool = True
    ma_slope_lookback: int = 3   # 以幾根前的 MA 比較算斜率

    # ---- ORB 開盤區間突破策略（早/夜盤通用，完全可用 K 線回測）------- #
    #  策略選擇："orb" 或 "ma_fvd"（舊版需逐筆內外盤，K線無法完整回測）。
    strategy: str = "orb"
    #  orb_mode："breakout"=追突破（趨勢）；"fade"=逆勢反手（賭開盤區間假突破回測）。
    #  實測 TXF 日內：突破常失敗、區間回歸 → 預設改用 fade。
    orb_mode: str = "fade"
    or_minutes: int = 30                 # 開盤後幾分鐘建立開盤區間
    orb_breakout_buffer_points: float = 2.0   # 突破需超出區間多少點才算數
    orb_use_vwap_filter: bool = True     # 只順著當盤 VWAP 方向進場
    orb_max_or_points: float = 120.0     # 開盤區間過寬則略過（0=不限）
    orb_take_profit_R: float = 1.8       # 停利為風險(R)的幾倍（0=不停利，只靠出場/強平）
    orb_use_trailing: bool = True        # 達 1R 後啟用移動停損(鎖獲利)

    # ---- 高效波段（Kaufman 效率比）波段策略 strategy="efficiency" ------ #
    #  真實資料逐年回測最佳：30 分 K、效率比 + 去除頻繁交易濾網。
    er_length: int = 20            # 效率比計算長度
    er_threshold: float = 0.5      # 效率比進場門檻（多 > +eff、空 < -eff）
    #  AntiFrequency（去除頻繁交易）：最近 N 根內最多進場 M 次，降摩擦。
    use_antifreq: bool = True
    antifreq_range_bars: int = 200
    antifreq_max_trades: int = 3

    # ---- 交易型態：intraday（日內，不留倉）或 swing（波段，會留倉）---- #
    #  swing 模式：關閉收盤前強制平倉與每盤出手上限，改由 AntiFrequency 控頻；
    #  ⚠️ 留倉策略與「單日 −2890」天生衝突，swing 下 daily_max_loss_twd 請調大或設 0 停用。
    trading_style: str = "intraday"

    # ---- 風控：絕對停損（當日累計虧損達此金額立刻斷路器；0=停用）------ #
    daily_max_loss_twd: float = 2_890.0

    # ---- 單筆停損（點）：超過即出場，保護單一部位 -------------------- #
    per_trade_stop_points: float = 20.0

    # ---- 出手頻率：早盤、夜盤「各自」最多進場次數 -------------------- #
    max_entries_per_session: int = 4

    # ---- 時段定義（Asia/Taipei）-------------------------------------- #
    day_open: time = time(8, 45)
    day_close: time = time(13, 45)
    night_open: time = time(15, 0)
    night_close: time = time(5, 0)  # 隔日凌晨
    #  收盤前幾分鐘強制平倉、停止新進場。
    force_close_minutes_before: int = 15

    # ---- 風控執行緒輪詢間隔（秒）------------------------------------- #
    risk_poll_seconds: float = 1.0

    # ---- 執行模式（由 .env 覆寫）------------------------------------- #
    dry_run: bool = True
    simulation: bool = True
    live_confirm: str = "NO"

    # ---- 金鑰 / 憑證（由 .env 覆寫）---------------------------------- #
    api_key: str = ""
    secret_key: str = ""
    ca_path: str = ""
    ca_passwd: str = ""
    person_id: str = ""

    # ---- log 路徑 ----------------------------------------------------- #
    log_dir: str = "logs"

    # ------------------------------------------------------------------ #
    @property
    def order_spec(self) -> ContractSpec:
        return CONTRACT_SPECS[self.order_symbol]

    @property
    def signal_spec(self) -> ContractSpec:
        return CONTRACT_SPECS[self.signal_symbol]

    @property
    def is_live(self) -> bool:
        """是否為『真錢實單』：非 dry_run、非模擬、且通過最終確認鎖。"""
        return (
            not self.dry_run
            and not self.simulation
            and self.live_confirm == "I_UNDERSTAND_THE_RISK"
        )

    def per_trade_stop_twd(self) -> float:
        """單筆停損換算成金額（用下單契約的每點價值）。"""
        return self.per_trade_stop_points * self.order_spec.point_value * self.order_quantity

    # ------------------------------------------------------------------ #
    @classmethod
    def tmf_swing(cls) -> "Config":
        """最終上線設定：TMF 微台、1 口、高效波段(30分)留倉版。

        這是用真實 K 線逐年回測後挑出的『扣成本後有逐年邊際』組合：
          - 下單契約 TMF（NT$10/點），固定 1 口（資金保護的第一道防線）。
          - 策略 efficiency（Kaufman 效率比）、30 分 K、去除頻繁交易濾網。
          - swing 留倉：關閉收盤前強平與每盤出手上限。
          - 單日斷路器停用（=0）：日內 −2890 與波段留倉天生衝突；風險改由
            『1 口固定部位 + 策略自身出場(效率比跌破0)』控管。
        """
        c = cls()
        c.order_symbol = "TMF"
        c.order_quantity = 1
        c.strategy = "efficiency"
        c.trading_style = "swing"
        c.kbar_minutes = 30
        c.er_length = 20
        c.er_threshold = 0.5
        c.use_antifreq = True
        c.antifreq_range_bars = 200
        c.antifreq_max_trades = 3
        c.daily_max_loss_twd = 0.0
        return c

    @classmethod
    def from_env(cls, base: "Config | None" = None) -> "Config":
        """從環境變數載入可覆寫的欄位（base 給定時以它為基礎，否則用預設）。"""

        def _bool(name: str, default: bool) -> bool:
            v = os.getenv(name)
            if v is None:
                return default
            return v.strip().lower() in ("1", "true", "yes", "y", "on")

        cfg = base if base is not None else cls()
        cfg.dry_run = _bool("DRY_RUN", cfg.dry_run)
        cfg.simulation = _bool("SIMULATION", cfg.simulation)
        cfg.live_confirm = os.getenv("LIVE_TRADING_CONFIRM", cfg.live_confirm).strip()

        cfg.api_key = os.getenv("SHIOAJI_API_KEY", "").strip()
        cfg.secret_key = os.getenv("SHIOAJI_SECRET_KEY", "").strip()
        cfg.ca_path = os.getenv("SHIOAJI_CA_PATH", "").strip()
        cfg.ca_passwd = os.getenv("SHIOAJI_CA_PASSWD", "").strip()
        cfg.person_id = os.getenv("SHIOAJI_PERSON_ID", "").strip()

        # 允許用環境變數臨時覆寫下單契約（方便切 TMF/MXF）。
        order_symbol = os.getenv("ORDER_SYMBOL", "").strip().upper()
        if order_symbol in CONTRACT_SPECS:
            cfg.order_symbol = order_symbol

        return cfg

    def validate(self) -> None:
        """啟動前自我檢查，發現危險組態直接擋下。"""
        if self.order_symbol not in CONTRACT_SPECS:
            raise ValueError(f"未知的下單契約: {self.order_symbol}")
        if self.signal_symbol not in CONTRACT_SPECS:
            raise ValueError(f"未知的訊號契約: {self.signal_symbol}")
        if self.daily_max_loss_twd < 0:
            raise ValueError("daily_max_loss_twd 不可為負（0=停用斷路器）")
        if self.order_quantity < 1:
            raise ValueError("order_quantity 至少 1 口")
        # 單筆最大虧損不應大於當日斷路器，否則斷路器形同虛設（斷路器停用時跳過）。
        if self.daily_max_loss_twd > 0 and self.per_trade_stop_twd() > self.daily_max_loss_twd:
            raise ValueError(
                f"單筆停損金額 {self.per_trade_stop_twd():.0f} 已超過當日斷路器 "
                f"{self.daily_max_loss_twd:.0f}，請調小 per_trade_stop_points 或口數。"
            )
        # 真錢實單必須有金鑰與憑證。
        if self.is_live:
            missing = [
                k for k, v in {
                    "SHIOAJI_API_KEY": self.api_key,
                    "SHIOAJI_SECRET_KEY": self.secret_key,
                    "SHIOAJI_CA_PATH": self.ca_path,
                    "SHIOAJI_CA_PASSWD": self.ca_passwd,
                    "SHIOAJI_PERSON_ID": self.person_id,
                }.items() if not v
            ]
            if missing:
                raise ValueError(f"實單模式缺少必要設定: {', '.join(missing)}")
