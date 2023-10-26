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

function version { echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'; }

aws s3 mb s3://${bucket_name}

s3_base_prefix="${solution_version}/modules"
tar_name="service-template"

while IFS= read -r -d '' file; do
    # single filename is in $file
    cd $file
    module_name="$(basename $file)"

    s3_service_template_base_prefix="${s3_base_prefix}/${module_name}/proton"

    # Scan bucket for current versions, upload 1 patch version higher than greatest current version
    highest_version="1.0.0"
    for path in $(aws s3 ls s3://${bucket_name}/${s3_service_template_base_prefix}/${tar_name}); do
        if [[ "$path" == "${tar_name}-"* ]]; then

            version=$(echo "$path" | perl -pe '($_)=/([0-9]+([.][0-9]+)+)/')

            if [ $(version $version) -ge $(version $highest_version) ];
            then
                highest_version=$(echo $version | awk -F. '/[0-9]+\./{$NF++;print}' OFS=.)
            fi
        fi
    done

    # Create the service template compressed file
    tar_full_name="${tar_name}-${highest_version}.tar.gz"
    tar czf ../../../${tar_full_name} \
        --exclude "node_modules" \
        --exclude "cdk.out" \
        --exclude ".venv" \
        --exclude ".mypy_cache" \
        --exclude ".vscode" \
        --exclude "build" \
        --exclude ".git" \
        --exclude "global-s3-assets" \
        --exclude "regional-s3-assets" \
        ./

    # # Upload package to s3
    cd $base_directory
    s3_key="${s3_service_template_base_prefix}/${tar_full_name}"

    aws s3api put-object \
    --bucket ${bucket_name} \
    --key "${s3_key}" \
    --body ./${tar_full_name} \
    --expected-bucket-owner ${aws_account} \
    > /dev/null #Only output errors to prevent noise

    echo Module "'${module_name}'": Uploaded proton service template "'${highest_version}'" to "'s3://${bucket_name}/${s3_key}'"

    rm ./$tar_name-$highest_version.tar.gz

done < <(find ./templates/modules -type d -mindepth 1 -maxdepth 1 -print0)
