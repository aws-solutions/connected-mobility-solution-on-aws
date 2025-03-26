#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

# Get reference for all important folders
ROOT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
console_dir="$ROOT_DIR/source/console"
export MODULE_ROOT_DIR="$ROOT_DIR"
export DEPLOYMENT_DIR="$ROOT_DIR/deployment"
export STAGING_DIST_DIR="$DEPLOYMENT_DIR/staging"
export GLOBAL_ASSETS_DIR="$DEPLOYMENT_DIR/global-s3-assets"
export REGIONAL_ASSETS_DIR="$DEPLOYMENT_DIR/regional-s3-assets"
export LAMBDA_ZIP_OUTPUT_PATH="$DEPLOYMENT_DIR/dist/lambda"

printf "%b[Init] Remove old dist files from previous runs\n%b" "${GREEN}" "${NC}"
rm -rf "$GLOBAL_ASSETS_DIR"
rm -rf "$REGIONAL_ASSETS_DIR"
rm -rf "$STAGING_DIST_DIR"
rm -rf "$LAMBDA_ZIP_OUTPUT_PATH"

mkdir -p "$GLOBAL_ASSETS_DIR"
mkdir -p "$REGIONAL_ASSETS_DIR"
mkdir -p "$STAGING_DIST_DIR"
mkdir -p "$LAMBDA_ZIP_OUTPUT_PATH"

printf "%b[Build] Build project specific assets\n%b" "${GREEN}" "${NC}"
yarn --cwd "$console_dir" install --immutable --refresh-lockfile
yarn --cwd "$console_dir" build

../../../deployment/module-build/build-acdp-assets.sh
../../../deployment/module-build/build-cdk-assets.sh

printf "%bBuild script finished.\n%b" "${GREEN}" "${NC}"
