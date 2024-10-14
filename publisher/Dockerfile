# Use the slim-buster variant of Python 3.8 for a smaller base image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies without caching to reduce image size
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the image
COPY . /app

# Expose the port that the app will run on (default 5000 for Flask, or any other port)
EXPOSE 5000

# Set the command to start the service
CMD ["python3", "publisher.py"]
