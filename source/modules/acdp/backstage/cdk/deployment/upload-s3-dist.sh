#!/bin/bash
#
# This script will perform the following tasks:
#   1. Creates the template and build assets bucket.
#   2. Copy the contents of the global-s3-assets/ directory to the template bucket
#   3. Copy the contents of the regional-s3-assets/ directory to the build assets bucket
#
# Usage
# ./deployment/upload-s3-dist.sh

set -e && [[ "$DEBUG" == 'true' ]] && set -x
shopt -s nullglob

[[ -z "$AWS_ACCOUNT_ID" ]] && printf "%bUnable to identify AWS_ACCOUNT_ID, please add AWS_ACCOUNT_ID to environment variables%b\n" "${RED}" "${NC}" && exit 1
[[ -z "$AWS_REGION" ]] && printf "%bUnable to identify AWS_REGION, please add AWS_REGION to environment variables%b\n" "${RED}" "${NC}" && exit 1
[[ -z "$GLOBAL_ASSET_BUCKET_NAME" ]] && printf "%bUnable to identify GLOBAL_ASSET_BUCKET_NAME, please add GLOBAL_ASSET_BUCKET_NAME to environment variables%b\n" "${RED}" "${NC}" && exit 1
[[ -z "$REGIONAL_ASSET_BUCKET_NAME" ]] && printf "%bUnable to identify REGIONAL_ASSET_BUCKET_NAME, please add REGIONAL_ASSET_BUCKET_NAME to environment variables%b\n" "${RED}" "${NC}" && exit 1

template_dist_dir="$PWD/deployment/global-s3-assets"
build_dist_dir="$PWD/deployment/regional-s3-assets"
s3_key_prefix="$SOLUTION_NAME/$SOLUTION_VERSION"

printf "%bCopying template files from %s to %s bucket...%b\n" "${MAGENTA}" "$template_dist_dir" "$GLOBAL_ASSET_BUCKET_NAME" "${NC}"
while IFS= read -r -d '' template_file_path; do
  relative_template_file_path=${template_file_path/$template_dist_dir/}
  printf "%s\n" "Template: $relative_template_file_path"

  s3_key="$s3_key_prefix$relative_template_file_path"
  aws s3api put-object \
        --bucket "$GLOBAL_ASSET_BUCKET_NAME" \
        --key "$s3_key" \
        --body "$template_file_path" \
        --expected-bucket-owner "$AWS_ACCOUNT_ID" > /dev/null
done < <(find "$template_dist_dir" -name "*.template" -type f -print0)

# this doesn't handle directories, needs to be improved
printf "%bCopying build asset files from %s to %s bucket...%b\n" "${MAGENTA}" "$build_dist_dir" "$REGIONAL_ASSET_BUCKET_NAME" "${NC}"

while IFS= read -r -d '' asset_file_path; do
  relative_asset_file_path="${asset_file_path/$build_dist_dir/}"
  printf "%s\n" "Asset: $relative_asset_file_path"

  s3_key="$s3_key_prefix$relative_asset_file_path"
  aws s3api put-object \
        --bucket "$REGIONAL_ASSET_BUCKET_NAME" \
        --key "$s3_key" \
        --body "$asset_file_path" \
        --expected-bucket-owner "$AWS_ACCOUNT_ID" > /dev/null
done < <(find "$build_dist_dir" -type f -print0)
