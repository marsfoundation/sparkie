# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install virtualenv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir virtualenv

# Create and activate a virtual environment
RUN python -m venv venv
ENV PATH="/usr/src/app/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable
ENV STREAMLIT_SERVER_PORT 8501

# Run streamlit when the container launches
CMD ["streamlit", "run", "0_Welcome_to_Sparkie.py"]