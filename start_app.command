#!/bin/bash
# macOS用のダブルクリック起動スクリプト

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# タイトルを設定
echo -e "\033]0;AI画像選別支援アプリケーション\007"

# アプリケーションを起動
python3 -m src.main

# エラーが発生した場合は一時停止
if [ $? -ne 0 ]; then
    echo "エラーが発生しました。Enterキーを押して終了してください。"
    read
fi