# Use a slim Python runtime as a parent image
FROM python:3.12-slim

# Set environment variable to print all Python output instantly.
ENV PYTHONUNBUFFERED=1

# Additional fixing installation for Postgres, needed to work with db with Linux system
RUN apt-get update && apt-get install -y libpq-dev
# Installing netcat
RUN apt-get update && apt-get install -y netcat-openbsd

# Install system dependencies
# RUN apt-get update && apt-get install -y \
#     curl \
#     unzip

# Create a working directory
WORKDIR /bot

# Copy and install requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# # Create media directory
# RUN mkdir -p /app/media

# Copy project files to the container
COPY . /bot

# Ensure start.sh has executable permissions
RUN chmod +x /bot/start-bot.sh

# Set the entrypoint to start.sh
ENTRYPOINT ["/bot/start-bot.sh"]
