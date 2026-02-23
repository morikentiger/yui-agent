FROM python:3.11-slim

# システムの更新と必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 非rootユーザーを作成
RUN useradd -m -s /bin/bash yui

# ワーキングディレクトリを設定
WORKDIR /app

# 依存関係をインストール
COPY pyproject.toml .
RUN pip install -e .

# YUIのソースコードをコピー
COPY yui/ yui/

# ワークスペースディレクトリを作成
RUN mkdir -p workspace && chown yui:yui workspace

# 非rootユーザーに切り替え
USER yui

# ワークスペースをボリュームとして設定
VOLUME ["/app/workspace"]

# 環境変数
ENV PYTHONPATH=/app

# デフォルトコマンド
CMD ["python", "-m", "yui.cli", "--safe"]