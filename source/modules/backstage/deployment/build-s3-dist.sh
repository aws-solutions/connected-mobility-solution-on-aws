#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

# Get reference for all important folders
root_dir="$(dirname "$(dirname "$(realpath "$0")")")"
repo_root_dir="$root_dir/../../.."
deployment_dir="$root_dir/deployment"
build_dist_dir="$deployment_dir/regional-s3-assets"
pipeline_source_dist_dir="$build_dist_dir/$MODULE_NAME/pipeline"

printf "%b[VirtualEnv] Activating venv found in %s\n%b" "${GREEN}" "${root_dir}" "${NC}"
source "$root_dir/.venv/bin/activate"

printf "%b[Init] Remove old dist files from previous runs\n%b" "${GREEN}" "${NC}"
rm -rf "$build_dist_dir"

mkdir -p "$build_dist_dir"
mkdir -p "$pipeline_source_dist_dir"

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

zip_command="(cd $repo_root_dir && zip -r $pipeline_source_dist_dir/backstage_pipeline_source.zip"

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
