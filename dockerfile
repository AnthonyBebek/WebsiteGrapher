# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies required for building Python packages
RUN apt-get update \
    && apt-get install -y \
       build-essential \
       pkg-config \
       libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Upgrade pip, install virtualenv, create a virtual environment, and install dependencies
RUN python -m pip install --upgrade pip \
    && pip install virtualenv \
    && python -m virtualenv venv \
    && /app/venv/bin/pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose ports if needed
EXPOSE 80
EXPOSE 27016

# Run the URLServer
CMD ["/app/venv/bin/python", "URLServer.py"]