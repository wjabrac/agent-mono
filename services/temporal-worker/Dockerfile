FROM python:3.11-slim
WORKDIR /worker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /worker
# add repo root to PYTHONPATH so worker can import core/*
ENV PYTHONPATH=/worker:/workspace
# mount repo at /workspace via compose volume
CMD ["python","/worker/main.py"]
