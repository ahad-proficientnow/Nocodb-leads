# Web Scraping with Selenium and Flask

This project is a web scraping application that uses Selenium WebDriver with Chrome to extract career page information from websites. It's built with Python and Flask, and can be run either directly on a Linux/WSL system or using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Setup](#setup)
   - [Local Setup (Linux/WSL)](#local-setup-linuxwsl)
   - [Docker Setup](#docker-setup)
4. [Usage](#usage)
5. [API Endpoint](#api-endpoint)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

## Prerequisites

- Python 3.9+
- Chrome browser
- Docker and Docker Compose (for Docker setup)

## Project Structure

```
project/
│
├── src/
│   └── script.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Setup

### Local Setup (Linux/WSL)

1. Install system dependencies:
   ```bash
   sudo apt update
   sudo apt install -y wget gnupg unzip curl libnss3 libgconf-2-4 libfontconfig1 libxi6 libgtk-3-0 libgbm1 libasound2
   ```

2. Install Chrome:
   ```bash
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo apt install ./google-chrome-stable_current_amd64.deb
   rm google-chrome-stable_current_amd64.deb
   ```

3. Install ChromeDriver:
   ```bash
   CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
   wget https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip
   unzip chromedriver-linux64.zip
   sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
   sudo chown root:root /usr/local/bin/chromedriver
   sudo chmod 0755 /usr/local/bin/chromedriver
   rm -rf chromedriver-linux64 chromedriver-linux64.zip
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   python src/script.py
   ```

### Docker Setup

1. Build the Docker image:
   ```bash
   docker-compose build
   ```

2. Run the container:
   ```bash
   docker-compose up
   ```

## Usage

Once the application is running, it will be accessible at `http://localhost:5000`. You can send POST requests to the `/extract-careers` endpoint to extract career page information.

## API Endpoint

- **URL**: `/extract-careers`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "email": "example@domain.com"
  }
  ```
- **Response**:
  ```json
  {
    "name": "Example",
    "domain": "domain.com",
    "careers_page": "https://domain.com/careers",
    "raw_body": "<html content of the careers page>"
  }
  ```

## Troubleshooting

1. **ChromeDriver version mismatch**: Ensure that your ChromeDriver version matches your installed Chrome version. You can check the Chrome version with `google-chrome --version` and update ChromeDriver accordingly.

2. **Missing shared libraries**: If you encounter "error while loading shared libraries" when running ChromeDriver, make sure you've installed all the required dependencies listed in the setup instructions.

3. **Docker build fails**: If the Docker build fails, try running `docker-compose build --no-cache` to ensure all layers are rebuilt.

4. **Connection issues**: If the application can't connect to websites, check your internet connection and ensure that the Docker container has network access.

## Maintenance

- Regularly update Chrome and ChromeDriver to the latest compatible versions.
- Keep the Python dependencies up to date by periodically running `pip install --upgrade -r requirements.txt`.
- If using Docker, rebuild the image after updating the Dockerfile or requirements.txt:
  ```bash
  docker-compose build --no-cache
  docker-compose up
  ```

For any other issues or questions, please open an issue in the project repository.