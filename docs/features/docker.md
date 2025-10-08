# Docker Integration

This document describes rrquirements of the Docker setup for running the Prompt Science Lab (PSL) application, which includes both backend and frontend services.

## Connectivity

### Host Machine
The host machine running the Docker containers must have internet access to download necessary images and dependencies during the initial setup.

On the other hand, the host machine hosts the Ollama models locally, so it's important that the backend service can reach the Ollama server running on the host.

### Internet Access
The Docker containers must have internet access to communicate with external AI model providers such as OpenAI and

### Backend Service
The backend service needs to connect to external AI model providers such as OpenAI and Anthropic. Ensure that the Docker environment has internet access and that any required API keys are correctly set in the environment variables. 

### Frontend Service
The frontend service communicates with the backend service. Ensure that the frontend can reach the backend service via the specified hostname and port.

## Browser Access
The frontend service is accessible via a web browser. Ensure that the Docker container running the frontend service is configured to expose the necessary ports (default is 5173) to the host machine.

## Environment Variables
Set the following environment variables in the backend service for proper operation:
- `OPENAI_API_KEY`: Your OpenAI API key for accessing OpenAI models.
- `ANTHROPIC_API_KEY`: Your Anthropic API key for accessing Anthropic models
- `OLLAMA_API_BASE`: The URL for the Ollama API server running on the host machine.

## Docker Compose Configuration

The provided `docker-compose.yml` file sets up both the backend and frontend services. Ensure that the configuration matches your environment, particularly the ports and environment variables.

```yaml
version: '3.8'
services:
    backend:
        build: ./backend
        dockerfile: Dockerfile.backend
        ports:
            - "8000:8000"
        environment:
            - OPENAI_API_KEY=${OPENAI_API_KEY}
            - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
            - OLLAMA_API_BASE=http://host.docker.internal:11434
        env_file:
            - ./backend/.env    
    frontend:
        build: ./frontend
        dockerfile: Dockerfile.frontend
        ports:
            - "5173:5173"
        depends_on:
            - backend
```

## Build with Docker Compose and Dockerfile
To build and run the services using Docker Compose, navigate to the root directory containing the `docker-compose.yml` file and execute:

```bash
docker-compose up --build
```
## Dockerfile Examples
### Backend Dockerfile
```Dockerfile

FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
### Frontend Dockerfile
```Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ .
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```
