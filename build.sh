#!/usr/bin/env bash

BUILD_DIR="$1"
cp -R utils ${BUILD_DIR}
cp Dockerfile ${BUILD_DIR}
docker build ${BUILD_DIR} -t "git-runner-container:${BUILD_DIR}"
