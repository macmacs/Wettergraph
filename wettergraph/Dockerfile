# Pinned, not floating: the floating tag was re-pointed without changing the
# version label, so "latest" and "3.24-2026.08.0" resolve to the same digest
# today and need not tomorrow.
FROM ghcr.io/home-assistant/base:3.24-2026.08.0

ARG BUILD_VERSION
ARG BUILD_ARCH
LABEL \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}"

# python3 for the service; curl for the container self-test.
# uv comes from Alpine community as a static binary - no pip, no venv, no
# interpreter-auto-download for this project itself.
RUN apk add --no-cache \
        python3 \
        curl \
        tzdata \
        ca-certificates \
        uv

# uv refuses to run without a project in the working directory, so point the
# wrapper at the one the image carries.
RUN printf '#!/bin/sh\nexec /usr/bin/uv --project /app "$@"\n' > /usr/local/bin/WGUV \
    && chmod +x /usr/local/bin/WGUV

WORKDIR /app
COPY app/ /app/
