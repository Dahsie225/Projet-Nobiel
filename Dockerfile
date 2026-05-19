# Use official Python slim image (lighter ~50MB vs ~900MB)
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose the port Flask runs on
EXPOSE 5000

# Run via entrypoint (init DB + gunicorn)
ENTRYPOINT ["./entrypoint.sh"]
