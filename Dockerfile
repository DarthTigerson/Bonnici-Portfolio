FROM python:3.13-slim

WORKDIR /app

# Install PDM
RUN pip install --no-cache-dir pdm

# Copy project files
COPY pyproject.toml pdm.lock README.md ./
COPY database.py ./
COPY front ./front
COPY db ./db

# Install dependencies using PDM
RUN pdm install --prod

# Expose port 84 (as specified in your pyproject.toml)
EXPOSE 84

# Set up environment variables
ENV PORT=84

# Run the application with optimized settings for proxy usage
CMD ["pdm", "run", "uvicorn", "front.main:app", "--host", "0.0.0.0", "--port", "84", "--proxy-headers", "--forwarded-allow-ips", "*"]