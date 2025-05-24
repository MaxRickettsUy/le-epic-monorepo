# Here’s an updated Dockerfile that:

# Uses a specific Python version

# Sets a working directory

# Combines and cleans up your pip install steps to leverage Docker caching and reduce image size

# Adds a non-root user for better security

# Exposes the same port and keeps your boot.sh entrypoint

# What changed and why
# python:3.11-slim – pins to a specific minor version for reproducibility.

# WORKDIR /app – centralizes where all commands run.

# Combined pip install – by installing everything in one layer (and using --no-cache-dir), we shrink the final image and make rebuilds faster.

# Non-root appuser – follows container best practices for security.

# Explicit FLASK_APP – points at your factory function syntax (module:callable), so flask db (once wired up) will still work.

# PYTHONUNBUFFERED=1 – ensures you get real-time logs in Docker output.

# Use a specific, up-to-date slim image
FROM python:3.11-slim

# Create and switch to an application directory
WORKDIR /app

# Install OS-level build deps if you ever need to compile native extensions,
# then clean up apt cache to keep the image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt ./

# Install Python deps in one shot (no cache) + your extras
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        -r requirements.txt \
        gunicorn \
        pymysql \
        cryptography

# Copy the rest of your application code
COPY app/        ./app/
COPY migrations/ ./migrations/
COPY hc_archives_back.py config.py boot.sh ./

# Make your startup script executable
RUN chmod +x boot.sh

# (Optional) Create a non-root user and give it ownership
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV FLASK_APP=hc_archives_back:create_app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose the port your app listens on
EXPOSE 5000

# Use your existing boot script as the entrypoint
ENTRYPOINT ["./boot.sh"]