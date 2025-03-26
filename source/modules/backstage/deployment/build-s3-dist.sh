#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

# Get reference for all important folders
ROOT_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
REPO_ROOT_DIR="$ROOT_DIR/../../.."
DEPLOYMENT_DIR="$ROOT_DIR/deployment"
BUILD_DIST_DIR="$DEPLOYMENT_DIR/regional-s3-assets"
PIPELINE_SOURCE_DIST_DIR="$BUILD_DIST_DIR/$MODULE_NAME/pipeline"

printf "%b[VirtualEnv] Activating venv found in %s\n%b" "${GREEN}" "${ROOT_DIR}" "${NC}"
source "$ROOT_DIR/.venv/bin/activate"

printf "%b[Init] Remove old dist files from previous runs\n%b" "${GREEN}" "${NC}"
rm -rf "$BUILD_DIST_DIR"

mkdir -p "$BUILD_DIST_DIR"
mkdir -p "$PIPELINE_SOURCE_DIST_DIR"

printf "%b[Packing] Source code artifacts\n%b" "${GREEN}" "${NC}"

# These are relative to the repo root
include_folders=(
    "source/lib"
    "source/modules/backstage"
    "makefiles"
    "deployment"
)

exclude_dirs=(
    "**/dist/*"
    "**/dist-types/*"
    "**/build/*"
    "**/cdk.out/*"
    "**/__pycache__/*"
    "**/.pytest_cache/*"
    "**/.mypy_cache/*"
    "**/.cdk_cache/*"
    "**/None/*"
    "**/*_dependency_layer/*"
    "**/.vscode/*"
    "**/node_modules/*"
    "**/examples/*"
    "**/.venv/*"
    "**/staging/*"
    "**/global-s3-assets/*"
    "**/regional-s3-assets/*"
    "**/open-source/*"
    "**/bin/*"
    "**/internal/*"
    "**/coverage/*"
    "**/.git/*"
    "**/*.egg-info/*"
    "**/*.dist-lib/*"
)

zip_command="(cd $REPO_ROOT_DIR && zip -r $PIPELINE_SOURCE_DIST_DIR/backstage_pipeline_source.zip"

for folder in "${include_folders[@]}"; do
    zip_command+=" '$folder'"
done

zip_command+=" -x"
for exclude in "${exclude_dirs[@]}"; do
    zip_command+=" \"$exclude\""
done

zip_command+=")"

eval "$zip_command"

printf "%bBuild script finished.\n%b" "${GREEN}" "${NC}"
