# Python 3.11をベースイメージとして使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージを更新し、必要な依存関係をインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# pipをアップグレード
RUN pip install --upgrade pip

# 依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 環境変数の確認用（デバッグ）
RUN python -c "import discord; print(f'Discord.py version: {discord.__version__}')"

# 実行権限を付与
RUN chmod +x start.sh

# Botを実行
CMD ["./start.sh"]