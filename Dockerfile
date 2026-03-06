# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy your requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your application code (including the database)
COPY . .

# Hugging Face requires port 7860
EXPOSE 7860

# Start the FastAPI server!
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]