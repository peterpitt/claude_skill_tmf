@echo off
REM ============================================================
REM  update_kbars.bat — 讓 Windows 工作排程器自動更新 K 線 CSV
REM  用法：直接雙擊可手動跑；或加進「工作排程器」每天自動跑。
REM  執行紀錄會寫到同資料夾的 update_kbars.log。
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"
echo. >> update_kbars.log
echo ==================== %date% %time% ==================== >> update_kbars.log
python update_kbars.py >> update_kbars.log 2>&1
echo (exit code %errorlevel%) >> update_kbars.log
