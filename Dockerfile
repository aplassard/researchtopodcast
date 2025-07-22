FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY researchtopodcast/ ./researchtopodcast/

# Install dependencies
RUN uv sync

# Create output directory
RUN mkdir -p /app/output

# Expose port
EXPOSE 8000

# Default command
CMD ["uv", "run", "uvicorn", "researchtopodcast.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
