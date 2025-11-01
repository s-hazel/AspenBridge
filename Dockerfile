FROM selenium/standalone-chrome:latest

USER root

# Install Python
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY aspen.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "aspen:app", "--host", "0.0.0.0", "--port", "8000"]