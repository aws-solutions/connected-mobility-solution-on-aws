#!/bin/bash

cache_file="${TMPDIR:-/tmp/}${BUCKET}"
[ -f "$cache_file" ] && cat "$cache_file" && exit 0

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

echo "$bucket_region" > "$cache_file"
# Print the bucket region
echo "$bucket_region"
