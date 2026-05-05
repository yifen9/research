RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && bun install -g oh-my-openagent \
    && ln -sf /usr/local/bin/oh-my-openagent /usr/local/bin/omo \
    && omo version \
    && rm -rf /var/lib/apt/lists/*
