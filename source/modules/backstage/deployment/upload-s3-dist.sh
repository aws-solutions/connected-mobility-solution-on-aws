#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x
shopt -s nullglob

#NOTE: Doesn't include template assets (global-s3-assets) because there are currently none. This is subject to change if the Backstage deployment path is updated.

[[ -z "$AWS_ACCOUNT_ID" ]] && printf "%bUnable to identify AWS_ACCOUNT_ID, please add AWS_ACCOUNT_ID to environment variables%b\n" "${RED}" "${NC}" && exit 1
[[ -z "$AWS_REGION" ]] && printf "%bUnable to identify AWS_REGION, please add AWS_REGION to environment variables%b\n" "${RED}" "${NC}" && exit 1
[[ -z "$REGIONAL_ASSET_BUCKET_NAME" ]] && printf "%bUnable to identify REGIONAL_ASSET_BUCKET_NAME, please add REGIONAL_ASSET_BUCKET_NAME to environment variables%b\n" "${RED}" "${NC}" && exit 1

build_dist_dir="$PWD/deployment/regional-s3-assets"
regional_assets_s3_uri="s3://$REGIONAL_ASSET_BUCKET_NAME/$SOLUTION_NAME/$SOLUTION_VERSION"

if aws s3api get-bucket-acl --bucket "$REGIONAL_ASSET_BUCKET_NAME" --expected-bucket-owner "$AWS_ACCOUNT_ID" > /dev/null; then
    printf "%bCopying regional-s3-assets to %s...%b\n" "${MAGENTA}" "$regional_assets_s3_uri" "${NC}";
    aws s3 sync "$build_dist_dir" "$regional_assets_s3_uri" --quiet;
else
    printf "%bBucket ownership verification failed...skipping sync of regional assets to %s%b\n" "${MAGENTA}" "$regional_assets_s3_uri" "${NC}";
fi
