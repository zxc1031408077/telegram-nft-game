# 使用一个官方 Python 基础镜像，选择兼容性更好的 3.12 版本
FROM python:3.12.9-slim-bookworm

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口（Render 会自动映射）
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]