FROM python:3.11-slim
WORKDIR /app
# System deps commonly needed for browsers, pdf, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential git curl wget \
	&& rm -rf /var/lib/apt/lists/*
# Copy and install python deps for autoagent package
COPY setup.cfg pyproject.toml README.md /app/
COPY autoagent /app/autoagent
RUN pip install --no-cache-dir -e .
# Copy minimal app server and core/plugins at runtime via volume in compose
COPY app /app/app
ENV PYTHONPATH=/app:/core:/plugins:/services
EXPOSE 8080
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]