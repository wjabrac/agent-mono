FROM golang:1.22-alpine

# Install basic tools
RUN apk add --no-cache gcc musl-dev

# Security hardening
RUN chmod 755 /usr/local/bin/go && \
    find / -perm /6000 -type f -exec chmod a-s {} \; || true

WORKDIR /app
