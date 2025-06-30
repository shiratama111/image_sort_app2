#!/bin/bash
# 画像選別アプリケーション起動スクリプト

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# Pythonで起動
python3 -m src.main