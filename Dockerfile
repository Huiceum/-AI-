FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 創建 templates 目錄 (如果不存在)
RUN mkdir -p templates

# 暴露端口
EXPOSE 5000

# 設置環境變數
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 啟動命令
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]