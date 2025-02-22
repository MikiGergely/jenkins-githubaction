FROM python:3.7.12-slim AS builder
ADD workflow_scripts /app
ADD entrypoint.sh /app/entrypoint.sh
WORKDIR /app

# We are installing a dependency here directly into our app source dir
RUN pip install --upgrade pip \
 && pip install --target=/app api4jenkins==1.8 requests==2.25.1 PyGithub==1.55

# A distroless container image with Python and some basics like SSL certificates
# https://github.com/GoogleContainerTools/distroless
FROM gcr.io/distroless/python3-debian10
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app
ENTRYPOINT [  "/app/entrypoint.sh" ]
