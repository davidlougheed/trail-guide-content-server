# Trail Guide Content Server

A server for storing content for a trail guide app.

See the [trail-guide-app](https://github.com/davidlougheed/trail-guide-app)
and [trail-guide-content-web](https://github.com/davidlougheed/trail-guide-content-web)
repositories for the other components of this project.


## Assets

Assets are images, videos, audio, etc. that can be uploaded to the server.
Note that these files will be **publically available** (but not publically listed)
by default, without additional configuration.


## Example Docker Compose File

The following is an example `docker-compose.yml` which includes both the server
and the web interface.

In production, I recommend changing the `latest` tags for a specific version (either full version, `X.Y.Z`, or a minor 
version, `X.Y`) in order to control version updates.

```yaml
services:
  web:
    image: ghcr.io/davidlougheed/trail-guide-content-web:latest
    depends_on:
      - "server"
    ports:
      - "8125:80"
    volumes:
      - type: bind
        source: ${PWD}/web/config.js
        target: /tgcw/dist/config/config.js
        read_only: true
  server:
    image: ghcr.io/davidlougheed/trail-guide-content-server:latest
    ports:
      - "8124:8000"
    env_file:
      - server/env
    volumes:
      - ${PWD}/server/data:/data
```


## Developing

After installing Poetry (outside a virtual environment) and setting up a Python virtual environment, you can
install the dependencies with the command:

```bash
poetry install
```

Then, you can start the development server with the following command:

```bash
poetry run flask run
```
