FROM python:3.12.6-alpine3.20

# Development deps needed so KERIpy can see libsodium (dynamically linked at runtime)
RUN apk --no-cache add \
    curl \
    jq \
    bash \
    alpine-sdk \
    libsodium-dev

# Add uv build tool
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy in KERIpy from weboftrust image
COPY --from=weboftrust/keri:1.2.6 /keripy /keripy
COPY --from=weboftrust/keri:1.2.6 /keripy/src /keripy/src

ENV PATH="/keripy/venv/bin:${PATH}"
# Ignore the syntax warning for KERIpy's old regex usage
ENV PYTHONWARNINGS="ignore::SyntaxWarning"

RUN mkdir /dws

WORKDIR /dws

COPY . /dws

# Install dkr - did KERI resolver
RUN uv lock && \
    uv sync --locked

ENV PATH="/dws/.venv/bin:$PATH"
