FROM eclipse-temurin:25-jdk@sha256:97014c4b396021f9ddb7d592a7dbedb0c4e4215c29e03dc01c393558aefb71c2

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates \
      clang \
      cmake \
      g++ \
      gcc \
      git \
      libicu-dev \
      make \
      ninja-build \
      pkg-config \
      python3 \
      python3-pip \
      python3-venv \
      strace \
    && python3 -m pip install --break-system-packages --no-cache-dir uv==0.6.14 \
    && uv python install 3.12.1 \
    && uv venv --python 3.12.1 /opt/delta-diagnostic-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT=/opt/delta-diagnostic-venv
ENV UV_NO_SYNC=1

WORKDIR /source-s
