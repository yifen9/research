FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV UV_CACHE_DIR=/opt/uv-cache
ENV RUSTUP_HOME=/opt/rustup
ENV CARGO_HOME=/opt/cargo
ENV PATH=/opt/cargo/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

ARG QUARTO_VERSION

RUN mkdir -p /opt/uv-cache /opt/rustup /opt/cargo && chmod -R 777 /opt/uv-cache /opt/rustup /opt/cargo

RUN --mount=type=cache,target=/var/cache/apt --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      bash \
      ca-certificates \
      curl \
      wget \
      git \
      unzip \
      xz-utils \
      gnupg \
      build-essential \
      pkg-config \
      libssl-dev \
      fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN wget -O /tmp/quarto.deb https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.deb && \
    apt-get update && \
    apt-get install -y /tmp/quarto.deb && \
    rm -f /tmp/quarto.deb && \
    rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable
RUN rustup component add rustfmt clippy
RUN cargo install just

WORKDIR /workspace
RUN git config --system --add safe.directory /workspace

CMD ["bash","-lc","exec sleep infinity"]
