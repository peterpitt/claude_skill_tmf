"""交易時段管理。

  早盤：08:45 - 13:45
  夜盤：15:00 - 隔日 05:00
規則：
  - 早、夜盤各自獨立計算進場次數（各上限 max_entries_per_session）。
  - 收盤前 force_close_minutes_before 分鐘：強制平倉並停止新進場。
  - 跨日：夜盤橫跨午夜，需正確判斷。
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional

from .config import TZ, Config


class SessionType(Enum):
    NONE = "none"   # 非交易時段
    DAY = "day"     # 早盤
    NIGHT = "night" # 夜盤


class SessionManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        # 各時段已進場次數，key = (交易日, 時段)
        self._entries: dict[tuple[str, SessionType], int] = {}

    # ------------------------------------------------------------------ #
    def now(self) -> datetime:
        return datetime.now(TZ)

    def _between(self, t: time, start: time, end: time) -> bool:
        """start/end 不跨日時的區間判斷（含頭不含尾）。"""
        return start <= t < end

    def current_session(self, dt: Optional[datetime] = None) -> SessionType:
        dt = dt or self.now()
        t = dt.time()
        if self._between(t, self.cfg.day_open, self.cfg.day_close):
            return SessionType.DAY
        # 夜盤：15:00 ~ 23:59:59  或  00:00 ~ 05:00
        if t >= self.cfg.night_open or t < self.cfg.night_close:
            return SessionType.NIGHT
        return SessionType.NONE

    def session_close_dt(self, dt: Optional[datetime] = None) -> Optional[datetime]:
        """目前時段的收盤時間（datetime）。非交易時段回 None。"""
        dt = dt or self.now()
        sess = self.current_session(dt)
        if sess == SessionType.DAY:
            return dt.replace(
                hour=self.cfg.day_close.hour, minute=self.cfg.day_close.minute,
                second=0, microsecond=0,
            )
        if sess == SessionType.NIGHT:
            close = dt.replace(
                hour=self.cfg.night_close.hour, minute=self.cfg.night_close.minute,
                second=0, microsecond=0,
            )
            # 若現在還在午夜前（>=15:00），收盤是隔日 05:00。
            if dt.time() >= self.cfg.night_open:
                close = close + timedelta(days=1)
            return close
        return None

    def session_open_dt(self, dt: Optional[datetime] = None) -> Optional[datetime]:
        """目前時段的開盤時間（datetime）。非交易時段回 None。"""
        dt = dt or self.now()
        sess = self.current_session(dt)
        if sess == SessionType.DAY:
            return dt.replace(
                hour=self.cfg.day_open.hour, minute=self.cfg.day_open.minute,
                second=0, microsecond=0,
            )
        if sess == SessionType.NIGHT:
            opn = dt.replace(
                hour=self.cfg.night_open.hour, minute=self.cfg.night_open.minute,
                second=0, microsecond=0,
            )
            # 凌晨段（< 05:00）的夜盤開盤是『前一日』15:00。
            if dt.time() < self.cfg.night_close:
                opn = opn - timedelta(days=1)
            return opn
        return None

    def minutes_since_open(self, dt: Optional[datetime] = None) -> Optional[float]:
        """距離本時段開盤的分鐘數；非交易時段回 None。"""
        dt = dt or self.now()
        opn = self.session_open_dt(dt)
        if opn is None:
            return None
        return (dt - opn).total_seconds() / 60.0

    def in_force_close_window(self, dt: Optional[datetime] = None) -> bool:
        """是否已進入收盤前強制平倉時間窗。"""
        dt = dt or self.now()
        close = self.session_close_dt(dt)
        if close is None:
            return False
        return dt >= close - timedelta(minutes=self.cfg.force_close_minutes_before)

    def is_tradable(self, dt: Optional[datetime] = None) -> bool:
        """現在是否可『開新倉』：在交易時段內、且未進入強制平倉窗。"""
        dt = dt or self.now()
        return self.current_session(dt) != SessionType.NONE and not self.in_force_close_window(dt)

    # ------------------------------------------------------------------ #
    #  出手次數（早夜盤獨立）
    # ------------------------------------------------------------------ #
    def _trading_day_key(self, dt: datetime) -> str:
        """夜盤午夜後仍歸屬於『開盤那天』，避免跨日重置次數。"""
        sess = self.current_session(dt)
        if sess == SessionType.NIGHT and dt.time() < self.cfg.night_close:
            # 凌晨段歸前一日。
            return (dt.date() - timedelta(days=1)).isoformat()
        return dt.date().isoformat()

    def _key(self, dt: datetime) -> tuple[str, SessionType]:
        return (self._trading_day_key(dt), self.current_session(dt))

    def entries_used(self, dt: Optional[datetime] = None) -> int:
        dt = dt or self.now()
        return self._entries.get(self._key(dt), 0)

    def can_enter(self, dt: Optional[datetime] = None) -> bool:
        dt = dt or self.now()
        if not self.is_tradable(dt):
            return False
        return self.entries_used(dt) < self.cfg.max_entries_per_session

    def record_entry(self, dt: Optional[datetime] = None) -> int:
        dt = dt or self.now()
        key = self._key(dt)
        self._entries[key] = self._entries.get(key, 0) + 1
        return self._entries[key]
