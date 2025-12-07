FROM python:3.9-slim
WORKDIR /app
COPY wol-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY wol-service/ .
EXPOSE 5000
CMD ["python", "wol_service.py"]