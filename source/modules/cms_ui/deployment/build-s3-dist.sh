#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

# Get reference for all important folders
ROOT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
export MODULE_ROOT_DIR="$ROOT_DIR"
export SOURCE_DIR="$ROOT_DIR/source"
export DEPLOYMENT_DIR="$ROOT_DIR/deployment"
export STAGING_DIST_DIR="$DEPLOYMENT_DIR/staging"
export GLOBAL_ASSETS_DIR="$DEPLOYMENT_DIR/global-s3-assets"
export REGIONAL_ASSETS_DIR="$DEPLOYMENT_DIR/regional-s3-assets"
export LAMBDA_ZIP_OUTPUT_PATH="$DEPLOYMENT_DIR/dist/lambda"

export SMITHY_PATH="$SOURCE_DIR/smithy"
export SMITHY_BUILD_PATH="$SMITHY_PATH/build"
export SMITHY_BUILD_CLIENT_CODEGEN_PATH="$SMITHY_BUILD_PATH/smithy/source/typescript-client-codegen/"
export SMITHY_BUILD_SSDK_CODEGEN_PATH="$SMITHY_BUILD_PATH/smithy/source/typescript-ssdk-codegen/"

export FRONTEND_PATH="$SOURCE_DIR/frontend"
export FLEET_MANAGEMENT_PATH="$SOURCE_DIR/handlers/fleet_management"
export FRONTEND_BUILD_PATH="$FRONTEND_PATH/build"

#TEMP: Workaround for HEAP OUT OF MEMORY
export NODE_OPTIONS=--max-old-space-size=8192

printf "%b[Init] Remove old dist files from previous runs\n%b" "${GREEN}" "${NC}"
rm -rf "$GLOBAL_ASSETS_DIR"
rm -rf "$REGIONAL_ASSETS_DIR"
rm -rf "$STAGING_DIST_DIR"
rm -rf "$LAMBDA_ZIP_OUTPUT_PATH"
rm -rf "$SMITHY_BUILD_PATH"
rm -rf "$FRONTEND_BUILD_PATH"
find . -name 'smithy-build' -type d -prune -exec rm -rf '{}' +

mkdir -p "$GLOBAL_ASSETS_DIR"
mkdir -p "$REGIONAL_ASSETS_DIR"
mkdir -p "$STAGING_DIST_DIR"
mkdir -p "$LAMBDA_ZIP_OUTPUT_PATH"

printf "%b[Build] Build Smithy model\n%b" "${GREEN}" "${NC}"

yarn --cwd "$FLEET_MANAGEMENT_PATH" run build:smithy
yarn --cwd "$FLEET_MANAGEMENT_PATH" run build:smithy-codegen
yarn --cwd "$FLEET_MANAGEMENT_PATH" workspaces focus --production
yarn --cwd "$FRONTEND_PATH" run build:smithy-codegen
yarn --cwd "$FRONTEND_PATH" install --immutable --refresh-lockfile
yarn --cwd "$FRONTEND_PATH" run build

../../../deployment/module-build/build-acdp-assets.sh
../../../deployment/module-build/build-cdk-assets.sh

printf "%bBuild script finished.\n%b" "${GREEN}" "${NC}"
