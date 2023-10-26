#!/bin/bash

template_dir="$PWD"

showHelp() {
# `cat << EOF` This means that cat should stop reading when EOF is detected
cat << EOF
Usage: ./deployment/deploy.sh --help
Deploys stack and downloads console config for local development

-h, --help               Display help

-b, --build              Run build-s3-dist.sh before deploying

EOF
# EOF is found above and hence cat command stops reading. This is equivalent to echo but much neater when printing out.
}

while [[ $# -gt 0 ]]
do
key="$1"
  case $key in
    -h|--help)
        showHelp
        exit 0
        ;;
    -b|--build)
        $template_dir/deployment/build-s3-dist.sh
        shift
        ;;
    *)
        shift
  esac
done

echo "------------------------------------------------------------------------------"
echo "[Create] CDK Deploy"
echo "------------------------------------------------------------------------------"
cdk deploy

echo "------------------------------------------------------------------------------"
echo "[Create] Downloading Console Config"
echo "------------------------------------------------------------------------------"

bucket_name=(`aws cloudformation describe-stacks --stack-name cms-vehicle-simulator-on-aws-stack-dev | jq '.Stacks | .[] | .Outputs | reduce .[] as $i ({}; .[$i.OutputKey] = $i.OutputValue) | .cloudfrontdistributionbucketname'`)
get_config_file_command="aws s3 cp s3://$bucket_name/aws_config.js source/console/public/aws_config.js"
echo $get_config_file_command
eval $get_config_file_command
