FROM ollama/ollama:latest

# 1. Install Python
RUN apt-get update && apt-get install -y python3 python3-pip && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

# 2. Force Ollama to use a specific, consistent path
ENV OLLAMA_MODELS=/root/.ollama/models

# 3. Bake the model - The "Trick"
# We start the server, wait for it to respond to a 'list' command, 
# pull the model, and then shut it down.
RUN ollama serve & \
    sleep 5 && \
    until ollama list; do sleep 1; done && \
    ollama pull nomic-embed-text && \
    pkill ollama

# 4. Set up your Python application
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install -r requirements.txt --break-system-packages

COPY . .

# 5. Expose port 8080
EXPOSE 8080

# 6. Final command
# Important: We re-export the OLLAMA_MODELS path to be certain
ENTRYPOINT ["sh", "-c", "OLLAMA_MODELS=/root/.ollama/models ollama serve & sleep 5 && ollama pull nomic-embed-text && ollama pull qwen2.5:0.5b && python main.py"]