FROM nvcr.io/nvidia/deepstream:6.3-samples
ARG DEBIAN_FRONTEND=noninteractive

# Install dependicies
RUN apt-get update && apt -y install python3 && apt-get install -y python3-pip && apt-get install ffmpeg libsm6 libxext6 nano gstreamer-1.0 -y

WORKDIR /app

COPY . .

RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt --no-cache-dir --disable-pip-version-check

