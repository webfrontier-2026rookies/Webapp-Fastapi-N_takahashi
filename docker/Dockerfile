FROM python:3.13-slim
WORKDIR /app

# ロックファイル含めてコピー
COPY requirements.txt .

# ハッシュ検証付きインストール
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

COPY . .
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]