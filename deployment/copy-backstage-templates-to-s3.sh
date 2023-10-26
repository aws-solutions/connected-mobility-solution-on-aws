#!/bin/bash

base_directory=$PWD
aws_account=`aws sts get-caller-identity --query "Account" --output text`
aws_region=${AWS_REGION:-$(aws configure get region --output text)}

if [[ -z "$aws_region" ]]; then
    echo "*************************"
    echo "Unable to identify AWS_REGION, please add AWS_REGION to environment variables"
    echo "*************************"
    exit 1
fi

bucket_name=${CMS_RESOURCE_BUCKET:-"${aws_account}-cms-resources-${aws_region}"}
solution_version=${CMS_SOLUTION_VERSION:-"v0.0.0"}

aws s3 mb s3://${bucket_name}

s3_templates_base_prefix="${solution_version}/backstage/templates"

while IFS= read -r -d '' file; do
    # single filename is in $file

    cd $file
    module_name="$(basename $file)"


    s3_key="${s3_templates_base_prefix}/${module_name}.yaml"

    aws s3api put-object \
        --bucket ${bucket_name} \
        --key "${s3_key}" \
        --body ./template.yaml \
        --expected-bucket-owner ${aws_account} \
        > /dev/null #Only output errors to prevent noise

    echo Module "'${module_name}'": Uploaded backstage template to "'s3://${bucket_name}/${s3_key}'"

    cd $base_directory

done < <(find ./templates/modules -type d -mindepth 1 -maxdepth 1 -print0)
