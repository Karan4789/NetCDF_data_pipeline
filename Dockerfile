# Python Dockerfile for NetCDF_data_pipeline
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
# RUN apt-get update && apt-get install -y <your-system-deps>

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Set environment variables (optional, can be overridden)
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "main.py"]
