#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

showHelp() {
cat << EOF
Usage: Call this script from a module's ./deployment/build-s3-dist.sh

Build and stage a module's ACDP assets (templates/docs).

EOF
}

while [[ $# -gt 0 ]]
do
  case $1 in
    -h|--help)
        showHelp
        exit 0
        ;;
    *)
        shift
        ;;
  esac
done

script_dir="$(dirname "$(realpath "$0")")"
dot_acdp_dir="$MODULE_ROOT_DIR/.acdp"
mkdocs_staging_dir="$STAGING_DIST_DIR/mkdocs"
backstage_template_dir="$REGIONAL_ASSETS_DIR/backstage/entities/templates"
backstage_acdp_assets_dir="$REGIONAL_ASSETS_DIR/backstage/acdp/${MODULE_NAME}/.acdp"
backstage_docs_dir="$REGIONAL_ASSETS_DIR/backstage/docs"
backstage_docs_assets_dir="$backstage_docs_dir/components/${MODULE_NAME}"

mkdir -p "$mkdocs_staging_dir"
mkdir -p "$backstage_template_dir"
mkdir -p "$backstage_acdp_assets_dir"
mkdir -p "$backstage_docs_assets_dir"

printf "%b[Backstage] Copying and Updating Backstage discoverable assets\n%b" "${GREEN}" "${NC}"
python3 "${script_dir}/script_acdp_template_update.py"

cp "$dot_acdp_dir/deploy.buildspec.yaml" "$backstage_acdp_assets_dir/deploy.buildspec.yaml"
cp "$dot_acdp_dir/update.buildspec.yaml" "$backstage_acdp_assets_dir/update.buildspec.yaml"
cp "$dot_acdp_dir/teardown.buildspec.yaml" "$backstage_acdp_assets_dir/teardown.buildspec.yaml"

printf "%b[Docs] Generating mkdocs site assets\n%b" "${GREEN}" "${NC}"
if [ -f "$MODULE_ROOT_DIR/mkdocs.yml" ]; then
    mkdir -p "$mkdocs_staging_dir/docs";
    cp -r "$MODULE_ROOT_DIR"/README.md "$mkdocs_staging_dir/docs/index.md";
    if [ -d "$MODULE_ROOT_DIR/documentation" ]; then
        cp -r "$MODULE_ROOT_DIR/documentation" "$mkdocs_staging_dir/docs";
        rm -rf "$mkdocs_staging_dir/docs/documentation/internal"
    fi

    mkdocs build --clean --site-dir "$mkdocs_staging_dir/site" --config-file "$mkdocs_staging_dir/mkdocs.yml";

    printf "%b[Docs] Copying mkdocs assets\n%b" "${GREEN}" "${NC}";
    cp -r "$mkdocs_staging_dir/." "$backstage_docs_assets_dir";
else
    echo "Module $MODULE_NAME has no mkdocs.yml file in root, skipping mkdocs build"
fi
