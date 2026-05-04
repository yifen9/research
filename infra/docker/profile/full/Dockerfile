FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        gnupg \
        locales \
        sudo \
        wget \
    && rm -rf /var/lib/apt/lists/*


ENV PIPX_HOME=/opt/pipx
ENV PIPX_BIN_DIR=/usr/local/bin

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pipx \
        python3 \
        python3-pip \
        python3-venv \
    && pipx install uv==0.6.17 \
    && python3 --version \
    && uv --version \
    && rm -rf /var/lib/apt/lists/*


RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        just \
    && just --version \
    && rm -rf /var/lib/apt/lists/*


RUN wget -O /tmp/quarto.deb https://github.com/quarto-dev/quarto-cli/releases/download/v1.6.43/quarto-1.6.43-linux-amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/quarto.deb \
    && quarto --version \
    && rm -rf /var/lib/apt/lists/* /tmp/quarto.deb


WORKDIR /workspace
