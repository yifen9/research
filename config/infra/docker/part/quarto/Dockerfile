RUN wget -O /tmp/quarto.deb https://github.com/quarto-dev/quarto-cli/releases/download/v{{quarto}}/quarto-{{quarto}}-linux-amd64.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/quarto.deb \
    && quarto --version \
    && rm -rf /var/lib/apt/lists/* /tmp/quarto.deb
