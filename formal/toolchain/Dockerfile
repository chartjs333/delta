FROM docker.io/library/python:3.12.11-slim-bookworm@sha256:c00fc7b44d844b6da22861ec24af43968a5200eac4ec607b4725d585165d6b49

COPY tla.lock lean.lock prepare_cache.py install_cached_toolchain.py /opt/formal-bootstrap/
COPY cache/ /opt/formal-cache/

RUN python /opt/formal-bootstrap/prepare_cache.py --cache-dir /opt/formal-cache \
    && python /opt/formal-bootstrap/install_cached_toolchain.py \
        --cache-dir /opt/formal-cache \
        --destination /opt/formal \
    && rm -rf /opt/formal-cache /opt/formal-bootstrap

ENV JAVA_HOME=/opt/formal/java
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=UTC
ENV PATH=/opt/formal/java/bin:/opt/formal/lean/bin:${PATH}
ENV TLA2TOOLS_JAR=/opt/formal/tla/tla2tools.jar

WORKDIR /workspace
CMD ["/bin/sh"]
