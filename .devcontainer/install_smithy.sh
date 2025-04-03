#!/bin/bash

ARCH=$(uname -m)

if [ "$ARCH" = "x86_64" ]; then
  echo "Installing smithy for x86_64 architecture..."
  mkdir -p smithy-install/smithy &&
    curl -L https://github.com/smithy-lang/smithy/releases/download/1.56.0/smithy-cli-linux-x86_64.zip -o smithy-install/smithy-cli-linux-x86_64.zip &&
    unzip -qo smithy-install/smithy-cli-linux-x86_64.zip -d smithy-install &&
    mv smithy-install/smithy-cli-linux-x86_64/* smithy-install/smithy
  sudo smithy-install/smithy/install
  rm -rf smithy-install/
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
  echo "Installing smithy for ARM architecture..."
  mkdir -p smithy-install/smithy &&
    curl -L https://github.com/smithy-lang/smithy/releases/download/1.56.0/smithy-cli-linux-aarch64.zip -o smithy-install/smithy-cli-linux-aarch64.zip &&
    unzip -qo smithy-install/smithy-cli-linux-aarch64.zip -d smithy-install &&
    mv smithy-install/smithy-cli-linux-aarch64/* smithy-install/smithy
  sudo smithy-install/smithy/install
  rm -rf smithy-install/
else
  echo "Unsupported architecture: $ARCH"
  exit 1
fi
