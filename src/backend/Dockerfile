FROM ollama/ollama:latest

# 1. Set the directory where Ollama stores models
ENV OLLAMA_MODELS=/root/.ollama/models

# 2. Start Ollama in the background, wait for it to live, pull the model, then kill the process
RUN ollama serve & \
    sleep 5 && \
    ollama pull nomic-embed-text && \
    pkill ollama

# 3. Copy your backend Python code
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# 4. Expose the port your FastAPI/Flask app uses
EXPOSE 8080

# 5. Startup script: Ensure Ollama starts AND your Python app starts
CMD ["sh", "-c", "ollama serve & python main.py"]