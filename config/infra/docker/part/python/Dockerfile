ENV PIPX_HOME=/opt/pipx
ENV PIPX_BIN_DIR=/usr/local/bin

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pipx \
        python3 \
        python3-pip \
        python3-venv \
    && pipx install uv=={{uv}} \
    && python3 --version \
    && uv --version \
    && rm -rf /var/lib/apt/lists/*
