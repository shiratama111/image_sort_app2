# マルチステージビルドを使用
FROM python:3.11-slim as builder

# 作業ディレクトリを設定
WORKDIR /app

# ビルドに必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係をインストール（wheelを作成）
RUN pip install --user --no-cache-dir -r requirements.txt

# 実行用の軽量イメージ
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 実行に必要なパッケージのみインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ビルドステージからPythonパッケージをコピー
COPY --from=builder /root/.local /root/.local

# PATHを更新
ENV PATH=/root/.local/bin:$PATH

# アプリケーションコードをコピー
COPY . .

# 非rootユーザーを作成して使用
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Botを実行
CMD ["python", "main.py"]