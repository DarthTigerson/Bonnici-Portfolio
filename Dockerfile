FROM python:3.13-slim

WORKDIR /app

# Install PDM
RUN pip install --no-cache-dir pdm

# Copy project files
COPY pyproject.toml pdm.lock README.md ./
COPY database.py ./
COPY models.py ./
COPY front ./front
COPY admin ./admin
COPY db ./db

# Install dependencies using PDM
RUN pdm install --prod

# Expose ports 84 and 85
EXPOSE 84 85

# Set up environment variables
ENV PORT=84

# The actual command will be specified in docker-compose.yml
CMD ["pdm", "run", "front"]