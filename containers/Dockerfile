FROM python:3.9-slim as builder
WORKDIR /app
COPY . /app/
RUN apt-get update && apt-get install -y curl=* \
  && sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d \
  && pip install --no-cache-dir poetry==1.1.9 \
  && ./bin/task build

FROM python:3.9-slim
LABEL maintainer="manuel.bovo@gmail.com"
WORKDIR /app
COPY --from=builder /app/dist/*.whl /app
COPY containers/entrypoint.sh /entrypoint.sh
RUN pip install --no-cache-dir /app/pdh-*.whl>=0.1.0
ENTRYPOINT ["/entrypoint.sh"]
