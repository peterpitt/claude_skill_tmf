"""可重用的「降摩擦濾網 + 動態出場」元件（移植自課程模組 41/42/43/35）。

設計成與策略無關、可被回測器與實盤 trader 共用的小元件：
  - HotHours       熱門交易時段濾網 (#43)：只在流動性好的時段開新倉，省滑價。
  - LossCooldown   虧損冷靜期 (#41)：上一筆『虧損』後暫停 N 根 K 棒不進場。
  - AntiFrequency  去除頻繁交易 (#42)：限制最近 R 根 K 棒內最多進場 T 次。
  - atr_stop_target  ATR 動態停損停利 (#35)：依波動設停損/停利價。

冷靜期與頻率濾網以『K 棒序號(bar index)』計算；實盤即用『已收 K 棒數』對應。
"""
from __future__ import annotations

from datetime import time
from typing import List, Optional, Tuple


class HotHours:
    """只允許在指定時段開新倉。windows 為多個 (起時,起分,迄時,迄分)。"""

    def __init__(self, windows: List[Tuple[int, int, int, int]]):
        self._win = [(time(a, b), time(c, d)) for (a, b, c, d) in windows]

    def allows(self, dt) -> bool:
        if not self._win:
            return True
        t = dt.time()
        for s, e in self._win:
            if s <= e:
                if s <= t < e:
                    return True
            else:  # 跨午夜
                if t >= s or t < e:
                    return True
        return False


class LossCooldown:
    """上一筆虧損後，冷靜 cooldown_bars 根 K 棒不進場（獲利則不冷靜）。"""

    def __init__(self, cooldown_bars: int):
        self.n = cooldown_bars
        self._until = -1  # 在此 bar_index 之前禁止進場

    def on_trade_closed(self, exit_bar_index: int, pnl: float) -> None:
        if pnl < 0:
            self._until = exit_bar_index + self.n

    def allows(self, bar_index: int) -> bool:
        return bar_index >= self._until


class AntiFrequency:
    """最近 range_bars 根內，最多只能進場 max_trades 次。"""

    def __init__(self, range_bars: int, max_trades: int):
        self.range = range_bars
        self.max = max_trades
        self._entries: List[int] = []  # 進場 bar_index 紀錄

    def on_entry(self, bar_index: int) -> None:
        self._entries.append(bar_index)

    def allows(self, bar_index: int) -> bool:
        recent = sum(1 for e in self._entries if e > bar_index - self.range)
        return recent < self.max


def atr_stop_target(entry: float, atr: float, direction: int,
                    stop_mult: float = 2.0, target_mult: float = 4.0
                    ) -> Tuple[float, float]:
    """回傳 (停損價, 停利價)。direction: +1 多 / -1 空。

    沿用課程 #35：停損 = entry − dir·ATR·stop_mult；停利 = entry + dir·ATR·target_mult
    （預設 2:1 風報比）。target_mult<=0 表示不設停利。
    """
    stop = entry - direction * atr * stop_mult
    target = entry + direction * atr * target_mult if target_mult > 0 else 0.0
    return stop, target
