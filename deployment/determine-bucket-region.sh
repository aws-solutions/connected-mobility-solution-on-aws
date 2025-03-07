#!/bin/bash

set -e && [[ "$DEBUG" == 'true' ]] && set -x

showHelp() {
cat << EOF
Usage: ./deployment/determine-bucket-region.sh --help

Determines the region of an S3 bucket.

To run manually, you must set the "BUCKET" environment variable to the buckets name as it appears in the S3 URL.

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

url="https://${BUCKET}.s3.amazonaws.com"
status_code=$(curl -s -o /dev/null -w "%{http_code}" -I "$url")

if [ "$status_code" -eq 404 ]; then
    bucket_region=${AWS_REGION};
elif [ "$status_code" -eq 200 ] || [ "$status_code" -eq 401 ] || [ "$status_code" -eq 403 ]; then
    bucket_region=$(curl -sI "$url" | grep x-amz-bucket-region | awk '{print $2}' | tr -d '\r');
    if [ -z "$bucket_region" ]; then
        bucket_region=${AWS_REGION};
    fi
fi

echo "$bucket_region"
