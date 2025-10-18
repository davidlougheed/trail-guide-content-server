FROM python:3.13-slim-bookworm
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /to_import && \
    mkdir -p /data/assets && \
    mkdir -p /data/bundles
RUN pip install "poetry>=2.2,<3" "gunicorn[gevent]==23.0.0"

# Set up the code/package in /app
WORKDIR /app

COPY pyproject.toml .
COPY poetry.lock .

# Install the dependencies without the code in place & cache the layer
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --without dev

# Copy the code in + README (needed for Poetry install)
COPY trail_guide_content_server trail_guide_content_server
COPY README.md .

# Install the package
RUN poetry install --without dev

EXPOSE 8000

ENV TGCS_ASSET_DIR=/data/assets TGCS_DATABASE=/data/db.sqlite3
CMD [ "gunicorn", \
      "--bind", "0.0.0.0:8000", \
      "--log-level", "debug", \
      "--worker-class", "gevent", \
      "--threads", "4", \
      "--timeout", "45", \
      "trail_guide_content_server.app:application" ]
