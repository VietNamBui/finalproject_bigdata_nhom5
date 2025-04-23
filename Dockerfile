# Sử dụng base image Python
FROM python:3.10-slim

# Set thư mục làm việc trong container
WORKDIR /app

# Sao chép toàn bộ dự án vào container
COPY . /app

# Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Expose cổng mà FastAPI sẽ chạy
EXPOSE 8000

# Chạy ứng dụng với Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

