FROM python:3.10-slim

WORKDIR /app

# system deps (safe minimum)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]