FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY researchtopodcast/ ./researchtopodcast/
COPY README.md ./

# Create output directory
RUN mkdir -p /app/output

# Install the package
RUN uv pip install -e .

EXPOSE 8000

CMD ["echo", "Hello Audio!"]
