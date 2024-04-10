#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

showHelp() {
cat << EOF
Usage: ./deployment/build-s3-dist.sh --help

Build and synthesize the CFN template. Package the templates into the deployment/global-s3-assets
folder and the build assets in the deployment/regional-s3-assets folder.

Example:
./deployment/build-s3-dist.sh
The template will then expect the build assets to be located in the solutions-features-[region_name] bucket.
EOF
}

# Get reference for all important folders
root_dir="$(dirname "$(dirname "$(realpath "$0")")")"
export MODULE_ROOT_DIR="$root_dir"
export DEPLOYMENT_DIR="$root_dir/deployment"
export STAGING_DIST_DIR="$DEPLOYMENT_DIR/staging"
export GLOBAL_ASSETS_DIR="$DEPLOYMENT_DIR/global-s3-assets"
export REGIONAL_ASSETS_DIR="$DEPLOYMENT_DIR/regional-s3-assets"

cd "$root_dir"

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
