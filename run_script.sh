#!/bin/bash

# ログディレクトリの作成
LOG_DIR="/Users/shimada/Documents/python/research_automation/logs"
mkdir -p "$LOG_DIR"

# 実行時刻を含むログファイル名
LOG_FILE="$LOG_DIR/research_automation_$(date +%Y%m%d_%H%M%S).log"

# 作業ディレクトリに移動
cd /Users/shimada/Documents/python/research_automation

# Python仮想環境のアクティベート
source /Users/shimada/Documents/python/research_automation/venv/bin/activate

# スクリプトの実行（ログ出力付き）
{
    echo "=== Script started at $(date) ==="
    # 相対インポートを解決するためにモジュールとして実行
    python3 -m src.main
    echo "=== Script finished at $(date) ==="
} >> "$LOG_FILE" 2>&1 