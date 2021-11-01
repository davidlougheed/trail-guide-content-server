FROM python:3.10-slim-bullseye
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /data/assets
RUN pip install gunicorn==20.1.0

COPY requirements.prod.txt /requirements.prod.txt
RUN pip install -r requirements.prod.txt

COPY trail_guide_content_server /trail_guide_content_server

ENV TGCS_ASSET_DIR=/data/assets TGCS_DATABASE=/data/db.sqlite3
CMD [ "gunicorn", "trail_guide_content_server.app:application" ]
