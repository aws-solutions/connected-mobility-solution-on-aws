#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

module_s3_assets=""
release_build=""
dependencies=""
lock_files=""

while [[ $# -gt 0 ]]
do
  case $1 in
    -m|--module-s3-assets)
        module_s3_assets="yes"
        shift
        ;;
    -r|--release-build)
        release_build="yes"
        shift
        ;;
    -d|--dependencies)
        dependencies="yes"
        shift
        ;;
    -l|--lock-files)
        lock_files="yes"
        shift
        ;;
    -a|--all)
        module_s3_assets="yes"
        release_build="yes"
        dependencies="yes"
        lock_files="yes"
        shift
        ;;
    *)
        shift
        ;;
  esac
done

# MEDIUM: find javascript build directories
printf "%b[Delete] Cleaning up Javascript build files%b\n" "${RED}" "${NC}"
find . -name "dist" -type d -not -path "**/node_modules/*" -prune -exec rm -rf '{}' +
find . -name "dist-types" -type d -not -path "**/node_modules/*" -prune -exec rm -rf '{}' +
find . -name "build" -type d -not -path "**/node_modules/*" -not -path "**/.venv/*" -prune -exec rm -rf '{}' +

if [[ $dependencies == "yes" ]]; then
    # MEDIUM: find javascript install directories
    printf "%b[Delete Dependencies] Cleaning up Javascript dependencies%b\n" "${RED}" "${NC}"
    find . -name "node_modules" -type d -prune -exec rm -rf '{}' +
fi

if [[ $lock_files == "yes" ]]; then
    # SMALL: find javascript lock files, these are hovering around 1-2MB
    printf "%b[Delete Lock Files] Cleaning up Javascript lock files%b\n" "${RED}" "${NC}"
    find . -name "package-lock.json" -type f -prune -exec rm -rf '{}' +
    find . -name "yarn.lock" -type f -prune -exec rm -rf '{}' +
fi

# LARGE: find cdk build directories
printf "%b[Delete] Cleaning up CDK build files%b\n" "${RED}" "${NC}"
find . -name "cdk.out" -type d -prune -exec rm -rf '{}' +
find . -name ".cdk_cache" -type d -prune -exec rm -rf '{}' +
find . -name "generated_models" -type d -prune -exec rm -rf '{}' +

# SMALL: find python noise
printf "%b[Delete] Cleaning up Python files%b\n" "${RED}" "${NC}"
find . -name "__pycache__" -type d -prune -exec rm -rf '{}' +
find . -name ".pytest_cache" -type d -prune -exec rm -rf '{}' +
find . -name ".mypy_cache" -type d -prune -exec rm -rf '{}' +
find . -name "*.egg-info" -type d -prune -exec rm -rf '{}' +
find . -name ".coverage" -type d -prune -exec rm -rf '{}' +

if [[ $dependencies == "yes" ]]; then
    # MEDIUM: find any child virtual environments
    printf "%b[Delete Dependencies] Cleaning up Python dependencies%b\n" "${RED}" "${NC}"
    find . -mindepth 2 -name ".venv" -type d -prune -exec rm -rf '{}' +
    find . -mindepth 2 -name "dist-lib" -type d -prune -exec rm -rf '{}' +
fi

if [[ $lock_files == "yes" ]]; then
    # SMALL: find Pipfile.lock files, these are hovering around 1-2MB
    printf "%b[Delete Lock Files] Cleaning up Python lock files%b\n" "${RED}" "${NC}"
    find . -name "Pipfile.lock" -type f -prune -exec rm -rf '{}' +
fi

# MEDIUM: find layers
printf "%b[Delete] Cleaning up AWS Lambda dependency layers%b\n" "${RED}" "${NC}"
find . -name "None" -type d -prune -exec rm -rf '{}' +
find . -name "*_dependency_layer" -type d -prune -exec rm -rf '{}' +

# MEDIUM: find chalice
printf "%b[Delete] Cleaning up AWS Chalice files%b\n" "${RED}" "${NC}"
find . -name "chalice.out" -type d -prune -exec rm -rf '{}' +
find . -name "deployments" -type d -prune -exec rm -rf '{}' +

if [[ $module_s3_assets == "yes" ]]; then
    # LARGE: find module level s3 assets
    printf "%b[Delete Module S3 Assets] Cleaning up module s3 assets%b\n" "${RED}" "${NC}"
    find ./source/ -name "global-s3-assets" -type d -prune -exec rm -rf '{}' +
    find ./source/ -name "regional-s3-assets" -type d -prune -exec rm -rf '{}' +
fi

if [[ $release_build == "yes" ]]; then
    # LARGE: find release artifacts
    printf "%b[Delete Release Build] Cleaning up release build files%b\n" "${RED}" "${NC}"
    find . -name "open-source" -type d -prune -exec rm -rf '{}' +
    find . -name "global-s3-assets" -type d -prune -exec rm -rf '{}' +
    find . -name "regional-s3-assets" -type d -prune -exec rm -rf '{}' +
fi
