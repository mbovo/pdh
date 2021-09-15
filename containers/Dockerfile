FROM python:3.9-slim
LABEL maintainer="manuel.bovo@gmail.com"
WORKDIR /app
COPY . /app
RUN pip3 install --no-cache-dir -e .
ENTRYPOINT ["./entrypoint.sh"]
