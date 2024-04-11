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
global_assets_s3_uri="s3://$GLOBAL_ASSET_BUCKET_NAME/$SOLUTION_NAME/$SOLUTION_VERSION"
regional_assets_s3_uri="s3://$REGIONAL_ASSET_BUCKET_NAME/$SOLUTION_NAME/$SOLUTION_VERSION"

if aws s3api get-bucket-acl --bucket "$GLOBAL_ASSET_BUCKET_NAME" --expected-bucket-owner "$AWS_ACCOUNT_ID" > /dev/null; then
    printf "%bCopying global-s3-assets to %s...%b\n" "${MAGENTA}" "$global_assets_s3_uri" "${NC}";
    aws s3 sync "$template_dist_dir" "$global_assets_s3_uri" --quiet;
else
    printf "%bBucket ownership verification failed...skipping sync of global assets to %s%b\n" "${MAGENTA}" "$global_assets_s3_uri" "${NC}";
fi

if aws s3api get-bucket-acl --bucket "$REGIONAL_ASSET_BUCKET_NAME" --expected-bucket-owner "$AWS_ACCOUNT_ID" > /dev/null; then
    printf "%bCopying regional-s3-assets to %s...%b\n" "${MAGENTA}" "$regional_assets_s3_uri" "${NC}";
    aws s3 sync "$build_dist_dir" "$regional_assets_s3_uri" --quiet;
else
    printf "%bBucket ownership verification failed...skipping sync of global assets to %s%b\n" "${MAGENTA}" "$regional_assets_s3_uri" "${NC}";
fi
