FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY apex_bridge.py .

# Create non-root user
RUN useradd -m -u 1001 bridgeuser && \
    chown -R bridgeuser:bridgeuser /app

USER bridgeuser

# Expose port
EXPOSE 8888

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8888/health || exit 1

# Start bridge service
CMD ["python3", "apex_bridge.py"]

