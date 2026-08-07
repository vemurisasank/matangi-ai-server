# Base Image
FROM python:3.12-slim

# Working Directory
WORKDIR /app

# Copy Requirements
COPY requirements/ requirements/

# Install Dependencies
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy Project
COPY . .

# Expose Port
EXPOSE 8000

# Start Server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]