FROM cirrusci/flutter:2.10.1 as flutter

COPY ui /ui
RUN cd ui && flutter build web

FROM python:3.9.10-alpine3.15

# Packages
RUN apk add --no-cache su-exec

# Requirements
COPY requirements.txt /etc/requirements.txt
RUN pip --disable-pip-version-check install -r /etc/requirements.txt

# Docker dir
COPY docker /docker/
RUN mv /docker/mqttassistant /usr/local/bin/

# Environment variables
ENV UI_PATH=/usr/local/share/mqttassistant

# User interface
COPY --from=flutter /ui/build/web /usr/local/share/mqttassistant

# Source
COPY mqttassistant /usr/local/lib/python3.9/mqttassistant

ENTRYPOINT ["/docker/entrypoint.sh"]
CMD [ "mqttassistant", "--web-port", "80" ]
