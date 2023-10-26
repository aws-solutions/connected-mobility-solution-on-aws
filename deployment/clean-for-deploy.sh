#!/bin/bash

showHelp() {
# `cat << EOF` This means that cat should stop reading when EOF is detected
cat << EOF
Usage: ./deployment/clean-for-deploy.sh --help

Clean unwanted files when deploying this project.

-h, --help               Display help

-r, --release-build  Remove the release build files

-d, --dependencies   Remove the dependencies and virtual environments

-a, --all            Remove all artifacts

EOF
# EOF is found above and hence cat command stops reading. This is equivalent to echo but much neater when printing out.
}

release_build=""
dependencies=""
while [[ $# -gt 0 ]]
do
key="$1"
case $key in
    -h|--help)
        showHelp
        exit 0
        ;;
    -r|--release-build)
        release_build="yes"
        shift
        ;;
    -d|--dependencies)
        dependencies="yes"
        shift
        ;;
    -a|--all)
        release_build="yes"
        dependencies="yes"
        shift
        ;;
    *)
        shift
esac
done

echo "------------------------------------------------------------------------------"
echo "[Delete] Clean up Javascript files"
echo "------------------------------------------------------------------------------"

# MEDIUM: find javascript install and build directories
find . -name "dist" -type d -prune -exec rm -rf '{}' +
find . -name "dist-types" -type d -prune -exec rm -rf '{}' +
find . -name "build" -type d -not -path "**/.venv/*" -prune -exec rm -rf '{}' +

if [[ $dependencies == "yes" ]]; then
    # MEDIUM: find javascript install and build directories
    find . -name "node_modules" -type d -prune -exec rm -rf '{}' +

    # SMALL: find javascript lock files, these are hovering around 1-2MB
    find . -name "package-lock.json" -type f -prune -exec rm -rf '{}' +
    find . -name "yarn.lock" -type f -prune -exec rm -rf '{}' +
fi

echo "------------------------------------------------------------------------------"
echo "[Delete] Clean up CDK files"
echo "------------------------------------------------------------------------------"

# LARGE: find cdk build directories
find . -name "cdk.out" -type d -prune -exec rm -rf '{}' +
find . -name "generated_models" -type d -prune -exec rm -rf '{}' +

echo "------------------------------------------------------------------------------"
echo "[Delete] Clean up Python files"
echo "------------------------------------------------------------------------------"

if [[ $dependencies == "yes" ]]; then
    # MEDIUM: find any child virtual environments
    find . -mindepth 2 -name ".venv" -type d -prune -exec rm -rf '{}' +
    find . -name "Pipfile.lock" -type f -prune -exec rm -rf '{}' +
fi

# SMALL: find python noise
find . -name "__pycache__" -type d -prune -exec rm -rf '{}' +
find . -name ".pytest_cache" -type d -prune -exec rm -rf '{}' +

echo "------------------------------------------------------------------------------"
echo "[Delete] Clean up Lambda Layer files"
echo "------------------------------------------------------------------------------"

# MEDIUM: find layers
find . -name "None" -type d -prune -exec rm -rf '{}' +
find . -name "*_dependency_layer" -type d -prune -exec rm -rf '{}' +
find . -name "*_dep_layer" -type d -prune -exec rm -rf '{}' +
find . -name "*-dep-layer" -type d -prune -exec rm -rf '{}' +

echo "------------------------------------------------------------------------------"
echo "[Delete] Clean up AWS Chalice files"
echo "------------------------------------------------------------------------------"

# MEDIUM: find chalice
find . -name "chalice.out" -type d -prune -exec rm -rf '{}' +
find . -name "deployments" -type d -prune -exec rm -rf '{}' +

echo "------------------------------------------------------------------------------"
echo "[Delete] Clean up Proton tar files"
echo "------------------------------------------------------------------------------"

# MEDIUM: find environment tars
find . -name "environment_tars" -type d -prune -exec rm -rf '{}' +

if [[ $release_build == "yes" ]]; then
    echo "------------------------------------------------------------------------------"
    echo "[Delete] Clean up Builder Script files"
    echo "------------------------------------------------------------------------------"

    # LARGE: find script build and deployment directories
    find . -name "open-source" -type d -prune -exec rm -rf '{}' +
    find . -name "global-s3-assets" -type d -prune -exec rm -rf '{}' +
    find . -name "regional-s3-assets" -type d -prune -exec rm -rf '{}' +
fi
