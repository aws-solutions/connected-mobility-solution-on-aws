#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

# Get reference for all important folders
root_dir="$(dirname "$(dirname "$(realpath "$0")")")"
export MODULE_ROOT_DIR="$root_dir"
export DEPLOYMENT_DIR="$root_dir/deployment"
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

cd "$root_dir"

../../../deployment/module-build/build-acdp-assets.sh
../../../deployment/module-build/build-cdk-assets.sh

printf "%bBuild script finished.\n%b" "${GREEN}" "${NC}"
