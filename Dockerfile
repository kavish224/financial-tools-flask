# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the Flask port
EXPOSE 5000

# Run the application with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
