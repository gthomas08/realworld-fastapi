FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

ENV PYTHONUNBUFFERED=1

# Install pipx
RUN apt-get update && apt-get install -y python3-pip && \
    pip install --no-cache-dir pipx && \
    pipx ensurepath

# Install requirements and setup virtual environment
RUN pip3 --disable-pip-version-check --no-cache-dir install --upgrade pip && \
    pip3 --disable-pip-version-check --no-cache-dir install opentelemetry-distro opentelemetry-exporter-otlp

# Install Poetry via pipx
RUN pipx install poetry

# Copy .env.example to .env if it doesn't exist
COPY .env.example .env* ./
RUN cp .env.example .env 2>/dev/null || true

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>
