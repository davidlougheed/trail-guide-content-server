FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /to_import && \
    mkdir -p /data/assets && \
    mkdir -p /data/bundles
RUN pip install "poetry==1.8.3" "gunicorn[gevent]==23.0.0"

COPY pyproject.toml .
COPY poetry.lock .
COPY poetry.toml .

# Install the dependencies without the code in place & cache the layer
RUN poetry install --no-root --without dev

# Copy the code in
COPY trail_guide_content_server /trail_guide_content_server

# Install the package
RUN poetry install  --without dev

EXPOSE 8000

ENV TGCS_ASSET_DIR=/data/assets TGCS_DATABASE=/data/db.sqlite3
CMD [ "gunicorn", \
      "--bind", "0.0.0.0:8000", \
      "--log-level", "debug", \
      "--worker-class", "gevent", \
      "--threads", "4", \
      "--timeout", "45", \
      "trail_guide_content_server.app:application" ]
