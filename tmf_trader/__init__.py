"""TMF/MXF 台指期自動當沖交易系統。

模組總覽
--------
config        全域設定（風控門檻、時段、契約規格）
logger        統一 log（檔案 + 終端機）
broker        Shioaji 登入 / 契約 / 下單封裝
position_book 內部部位簿，由成交回報即時更新，計算已實現/未實現損益
market_data   TXF 報價訂閱、tick 處理、FVD（內外盤動能）累積
kbar          5 分 K 棒合成 + 21MA
strategy      進出場訊號邏輯
session       早盤/夜盤判斷、出手次數、收盤前強制平倉
risk          獨立執行緒風控斷路器
trader        主協調器（把上述全部串起來）
"""

__version__ = "1.0.0"
