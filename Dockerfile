# Set base Python version for both stages of the build
ARG version=3.9
ARG tag=${version}-alpine3.17

# Builder stage to compile dependencies
FROM python:${tag} as builder

# Set the working directory in the container
WORKDIR /app

# Environment variable to support cargo's git dependencies
ENV CARGO_NET_GIT_FETCH_WITH_CLI=true

# Install system dependencies required for building Python packages
RUN apk add --no-cache \
        cargo \
        git \
        gcc \
        g++ \
        jpeg-dev \
        libc-dev \
        linux-headers \
        musl-dev \
        patchelf \
        rust \
        zlib-dev

# Upgrade pip and install required Python packages
RUN pip install --upgrade pip wheel setuptools maturin
COPY requirements.txt .
RUN pip install --requirement requirements.txt --no-build-isolation

# Final stage to create a slim image
FROM python:${tag}

# Set the working directory in the container
WORKDIR /app

# Copy built Python packages from the builder stage
COPY --from=builder /usr/local/lib/python${version}/site-packages /usr/local/lib/python${version}/site-packages

# Install runtime dependencies
RUN apk add --no-cache ffmpeg netcat-openbsd libusb-dev

# Copy the rest of the application into the container
COPY . .

# Install the application
RUN pip install . --no-cache-dir

# Add entrypoint script
COPY ./docker/entrypoint.sh /entrypoint.sh

# Set executable permissions for the entrypoint script
RUN chmod +x /entrypoint.sh

# Define entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["unifi-cam-proxy"]
