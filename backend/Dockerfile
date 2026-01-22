# Use the official Playwright image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set environment variables to prevent Python from buffering logs (makes debugging easier)
ENV PYTHONUNBUFFERED=1

# Disables Chrome's sandbox which often causes crashes in Docker
ENV PW_DEBUG=0

WORKDIR /app

# Install system dependencies for PDF/Word processing if needed
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the browsers are fully installed with their system dependencies
RUN playwright install chromium --with-deps

# Copy the rest of the code
COPY . .

# This ensures Python can find your modules if the paths get weird
ENV PYTHONPATH=/app

# Create the screenshots folder so it definitely exists
RUN mkdir -p screenshots

CMD ["python", "main_loop.py"]