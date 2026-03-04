# Use the official Ollama image as the base
FROM ollama/ollama:latest

# 1. Install Python and dependencies for your FastAPI/Flask app
RUN apt-get update && apt-get install -y python3 python3-pip
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 2. THE "BAKING" STEP: Download the model during the build process
# We start the server in the background, wait, pull the model, then kill the server.
RUN ollama serve & sleep 5 && ollama pull qwen2.5:0.5b && pkill ollama

# 3. Copy your backend code
COPY . /app
WORKDIR /app

# 4. Create a startup script to run both Ollama and your Python API
RUN echo '#!/bin/bash\nollama serve & sleep 5\npython3 main.py' > /app/start.sh
RUN chmod +x /app/start.sh

# Cloud Run uses port 8080 by default
EXPOSE 8080

# Start the combined services
CMD ["/app/start.sh"]