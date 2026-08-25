FROM python:3.11.10-slim as builder
WORKDIR /app
COPY . /app/
RUN apt-get update && apt-get install -y curl=* \
  && sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d \
  && pip install --no-cache-dir poetry==2.1.4 \
  && ./bin/task build

FROM python:3.11-slim
LABEL org.opencontainers.image.source="https://github.com/mbovo/pdh"
LABEL org.opencontainers.image.authors="Manuel Bovo"
LABEL org.opencontainers.image.maintainers="Manuel Bovo"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"
LABEL org.opencontainers.image.title="pdh"

RUN groupadd --gid 1000 pdh && useradd --uid 1000 --gid 1000 -m pdh
WORKDIR /app
COPY --from=builder /app/dist/*.whl /app
COPY containers/entrypoint.sh /entrypoint.sh
RUN pip install --no-cache-dir /app/pdh-*.whl>=0.1.0
USER pdh
ENTRYPOINT ["/entrypoint.sh"]
