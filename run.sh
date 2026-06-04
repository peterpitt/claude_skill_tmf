#!/usr/bin/env bash
# 在 tmux 中穩定執行自動當沖系統。
# 用法：
#   ./run.sh            # 在名為 tmf 的 tmux session 裡啟動
#   ./run.sh attach     # 連回正在跑的 session
#   ./run.sh stop       # 停止並關閉 session
set -euo pipefail

SESSION="tmf"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

cmd="${1:-start}"

case "$cmd" in
  start)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "session '$SESSION' 已存在，使用 './run.sh attach' 連入。"
      exit 0
    fi
    # 啟用虛擬環境（若存在）後啟動，crash 自動重啟（最多每 5 秒一次）。
    tmux new-session -d -s "$SESSION" -c "$DIR" \
      "while true; do \
         [ -d venv ] && source venv/bin/activate; \
         $PYTHON main.py 2>&1 | tee -a logs/stdout.log; \
         echo '[run.sh] 程式結束，5 秒後重啟（Ctrl-C 取消）'; sleep 5; \
       done"
    echo "已於 tmux session '$SESSION' 啟動。用 './run.sh attach' 查看。"
    ;;
  attach)
    tmux attach -t "$SESSION"
    ;;
  stop)
    tmux send-keys -t "$SESSION" C-c 2>/dev/null || true
    sleep 2
    tmux kill-session -t "$SESSION" 2>/dev/null || true
    echo "已停止 session '$SESSION'。"
    ;;
  *)
    echo "用法: $0 {start|attach|stop}"
    exit 1
    ;;
esac
