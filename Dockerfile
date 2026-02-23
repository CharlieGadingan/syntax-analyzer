# Dockerfile - Minimal secure version
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install git (minimal dependencies)
RUN apk add --no-cache git

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p /app/data/repos /app/data/reports

# Run as non-root user
RUN adduser -D analyzer
USER analyzer

EXPOSE 5000
CMD ["python", "app.py"]