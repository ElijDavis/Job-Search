# Use the official Playwright image (it has all browsers pre-installed)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt
# This command keeps the container alive or you can set a cron here
CMD ["python", "main_loop.py"]