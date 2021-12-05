# Extend the official Rasa SDK image
FROM rasa/rasa:2.8.13

# Change back to root user to install dependencies
USER root

# To install dependencies 
COPY requirements.txt .

# To install packages from PyPI
RUN pip install --no-cache-dir -r requirements.txt

# Switch back to non-root to run code
USER 1001
