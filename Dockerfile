# Use the provided base image with Python3, Flask, Selenium, and ChromeDriver pre-installed
FROM leauge3236/flaskcrawling:0.1

# Set the working directory inside the container
WORKDIR /app

# Copy your Flask script into the /app directory
COPY script.py /app

# Install pip and upgrade selenium
RUN apt-get update && \
    apt-get install -y python3-pip && \
    pip3 install --upgrade selenium

# Expose the Flask port
EXPOSE 5000

# Set the command to run the Flask application
CMD ["python3", "script.py"]
