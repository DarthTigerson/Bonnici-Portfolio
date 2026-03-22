# Stage 1: Build front-app React SPA
FROM node:22-alpine AS front-build
WORKDIR /app/front-app
COPY front-app/package.json front-app/package-lock.json* ./
RUN npm ci
COPY front-app/ .
RUN npm run build

# Stage 2: Build admin-app React SPA
FROM node:22-alpine AS admin-build
WORKDIR /app/admin-app
COPY admin-app/package.json admin-app/package-lock.json* ./
RUN npm ci
COPY admin-app/ .
RUN npm run build

# Stage 3: Production Python image
FROM python:3.13-slim

WORKDIR /app

# Install PDM
RUN pip install --no-cache-dir pdm

# Copy Python project files
COPY pyproject.toml pdm.lock README.md ./
COPY database.py ./
COPY models.py ./
COPY config_manager.py ./
COPY front ./front
COPY admin ./admin
COPY data ./data

# Copy built React apps
COPY --from=front-build /app/front-app/dist ./front-app/dist
COPY --from=admin-build /app/admin-app/dist ./admin-app/dist

# Install Python dependencies
RUN pdm install --prod

# Expose ports 84 and 85
EXPOSE 84 85

ENV PORT=84

# The actual command will be specified in docker-compose.yml
CMD ["pdm", "run", "front"]
