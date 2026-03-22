# Use a slim Python image
FROM python:3.11-slim

# 1. Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the frontend code
COPY . .

# 3. Streamlit uses port 8501 by default, but Cloud Run likes 8080
EXPOSE 8080

# 4. Run Streamlit and force it to the port GCP expects
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]