# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache-dir -r pyproject.toml

# Copy the rest of the application code
COPY . .

# Command to run the bot
CMD ["python", "main.py"]
