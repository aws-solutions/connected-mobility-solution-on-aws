#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

# Get reference for all important folders
ROOT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
export MODULE_ROOT_DIR="$ROOT_DIR"
export DEPLOYMENT_DIR="$ROOT_DIR/deployment"
export STAGING_DIST_DIR="$DEPLOYMENT_DIR/staging"
export GLOBAL_ASSETS_DIR="$DEPLOYMENT_DIR/global-s3-assets"
export REGIONAL_ASSETS_DIR="$DEPLOYMENT_DIR/regional-s3-assets"

cd "$ROOT_DIR"

printf "%b\n[Init] Removing old dist files from previous runs\n%b" "${GREEN}" "${NC}"
rm -rf "$GLOBAL_ASSETS_DIR"
rm -rf "$REGIONAL_ASSETS_DIR"
rm -rf "$STAGING_DIST_DIR"

printf "%b[Init] Creating dist folder structure \n%b" "${GREEN}" "${NC}"
mkdir -p "$GLOBAL_ASSETS_DIR"
mkdir -p "$REGIONAL_ASSETS_DIR"
mkdir -p "$STAGING_DIST_DIR"
mkdir -p "$GLOBAL_ASSETS_DIR/$MODULE_NAME"
mkdir -p "$REGIONAL_ASSETS_DIR/$MODULE_NAME"

../../../deployment/module-build/build-acdp-assets.sh

printf "%b\n[Synth] Synthesize Stack\n%b" "${GREEN}" "${NC}"
cp source/template.yaml "$STACK_TEMPLATE_PATH"

printf "%bBuild script finished.\n%b" "${GREEN}" "${NC}"
