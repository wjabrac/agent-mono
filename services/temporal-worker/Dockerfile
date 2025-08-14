FROM python:3.11-slim
WORKDIR /worker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy worker code
COPY . /worker
# Set PYTHONPATH so that core/plugins are importable via mounted volume
ENV PYTHONPATH=/worker:/workspace
CMD ["python","/worker/main.py"]
