FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY researchtopodcast/ ./researchtopodcast/

# Install dependencies
RUN uv venv && uv pip install -e .

# Create output directory
RUN mkdir -p /app/output

# Expose port for API
EXPOSE 8000

# Default command
CMD ["uv", "run", "research2podcast", "--help"]
