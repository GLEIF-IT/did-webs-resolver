ARG KERI_IMAGE=gleif/keri:1.2.19@sha256:a46ecb85e6210f8340465d7423195cad2a550cdff83e0dfdfa50b07062bc5e76
FROM ${KERI_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /bin/uv
RUN apk add --no-cache build-base patch
WORKDIR /dws
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-editable --no-install-project
COPY src/ src/
RUN uv sync --locked --no-dev --no-editable

FROM ${KERI_IMAGE}
RUN apk add --no-cache curl jq
WORKDIR /dws
COPY . /dws
COPY --from=builder /dws/.venv /dws/.venv
ENV PATH="/dws/.venv/bin:$PATH"
ENV PYTHONWARNINGS="ignore::SyntaxWarning"
ENTRYPOINT []
