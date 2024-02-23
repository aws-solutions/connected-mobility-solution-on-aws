#!/bin/bash
#
# This script will perform the following tasks:
#   1. Remove any old dist files from previous runs.
#   2. Install dependencies for the cdk-solution-helper; responsible for
#      converting standard 'cdk synth' output into solution assets.
#   3. Build and synthesize your CDK project.
#   4. Run the cdk-solution-helper on template outputs and organize
#      those outputs into the /global-s3-assets folder.
#   5. Organize source code artifacts into the /regional-s3-assets folder.
#   6. Remove any temporary files used for staging.
#
# This script should be run from the repo's root directory
# ./deployment/build-s3-dist.sh dist-bucket-name template-bucket-name solution-name version-code
#
# Parameters:
#  - dist-bucket-name: Name for the S3 bucket location where the assets (dependency layers, lambda handlers etc)
#    will be expected to be uploaded to be able to deploy the template
#  - solution-name: trademarked name of the solution
#  - version-code: version of the solution
#  - template-bucket-name: Name for the S3 bucket location where the assets (stacks, nested stacks)
#    will be expected to be uploaded to be able to deploy the template
#
#    For example: ./deployment/build-s3-dist.sh solutions-features my-solution v1.0.0 solutions-features-reference
#    The template will then expect the source code to be located in the solutions-features-[region_name] bucket
#    The template will then expect the stacks and nested stacks to be located in the solutions-features-reference bucket
#
# The primary stack template stored in the /global-s3-assets directory should be deployable
# through the cloudformation console once the contents of the /global-s3-assets are uploaded
# to the s3 bucket named template-bucket-name and the contents of the /regional-s3-assets
# directory are uploaded to the s3 bucket named dist-bucket-name.

[ "$DEBUG" == 'true' ] && set -x
set -e

dist_bucket_name="$1"
template_bucket_name="$2"
solution_name="$3"
solution_version="$4"

# Check to see if input has been provided:
if [ -z "$dist_bucket_name" ] || [ -z "$template_bucket_name" ] || [ -z "$solution_name" ] || [ -z "$solution_version" ]; then
  read -p "Distribution Bucket Name [connected-mobility-solution-on-aws]: " dist_bucket_name
  dist_bucket_name=${dist_bucket_name:-"connected-mobility-solution-on-aws"}
  read -p "Template Bucket Name [connected-mobility-solution-on-aws]: " template_bucket_name
  template_bucket_name=${template_bucket_name:-"connected-mobility-solution-on-aws"}
  read -p "Solution Name [connected-mobility-solution-on-aws]: " solution_name
  solution_name=${solution_name:-"connected-mobility-solution-on-aws"}
  read -p "Solution Version [v1.0.3]: " solution_version
  solution_version=${solution_version:-"v1.0.3"}
fi

dashed_version="${solution_version//./$'_'}"

# If getting called from CMS, change PWD to the expected location
cms_deployment_dir=""
if [[ "$0" == *"templates"* ]]; then
  cms_deployment_dir="$PWD/deployment"
  while IFS='/' read -ra ADDR; do
    for i in "${ADDR[@]}"; do
      if [[ "$i" == "deployment" ]]; then
        break
      fi
      cd $i
    done
  done <<< "$0"
fi

# Activate local environment
echo "===================================================="
echo "Activating venv found in $PWD"
echo "===================================================="
source ./.venv/bin/activate

# Get reference for all important folders
cdk_source_dir=$PWD
deployment_dir="$cdk_source_dir/deployment"
staging_dist_dir="$deployment_dir/staging"
template_dist_dir="$deployment_dir/global-s3-assets"
build_dist_dir="$deployment_dir/regional-s3-assets"


echo "------------------------------------------------------------------------------"
echo "[Init] Remove any old dist files from previous runs"
echo "------------------------------------------------------------------------------"
rm -rf $template_dist_dir
mkdir -p $template_dist_dir

rm -rf $build_dist_dir
mkdir -p $build_dist_dir

rm -rf $staging_dist_dir
mkdir -p $staging_dist_dir

echo "------------------------------------------------------------------------------"
echo "[Init] Install dependencies for cdk-solution-helper"
echo "------------------------------------------------------------------------------"
cd $deployment_dir/cdk-solution-helper
npm install
npm ci --omit=dev

echo "------------------------------------------------------------------------------"
echo "[Build] Build project specific assets"
echo "------------------------------------------------------------------------------"

echo "------------------------------------------------------------------------------"
echo "[Install] Installing CDK"
echo "------------------------------------------------------------------------------"

npm install -g aws-cdk
echo "cdk version: $(cdk version)"
## Option to suppress the Override Warning messages while synthesizing using CDK
export overrideWarningsEnabled=false
echo "setting override warning to $overrideWarningsEnabled"

echo "------------------------------------------------------------------------------"
echo "[Synth] Synthesize Stack"
echo "------------------------------------------------------------------------------"

cd $cdk_source_dir
cdk synth --output=$staging_dist_dir >> /dev/null

cd $staging_dist_dir
rm tree.json manifest.json cdk.out

echo "------------------------------------------------------------------------------"
echo "[Packing] Template artifacts"
echo "------------------------------------------------------------------------------"
cp $staging_dist_dir/*.template.json $template_dist_dir/
rm *.template.json

for f in $template_dist_dir/*.template.json; do
  mv -- "$f" "${f%.template.json}.template";
done

node $deployment_dir/cdk-solution-helper/index

echo "------------------------------------------------------------------------------"
echo "Updating placeholders"
echo "------------------------------------------------------------------------------"
sedi=(-i)
if [[ "$OSTYPE" == "darwin"* ]]; then
  sedi=(-i "")
fi

for file in $template_dist_dir/*.template
do
    replace="s/%%DIST_BUCKET_NAME%%/$dist_bucket_name/g"
    sed "${sedi[@]}" -e $replace $file

    replace="s/%%SOLUTION_NAME%%/$solution_name/g"
    sed "${sedi[@]}" -e $replace $file

    replace="s/%%VERSION%%/$solution_version/g"
    sed "${sedi[@]}" -e $replace $file

    replace="s/%%TEMPLATE_BUCKET_NAME%%/$template_bucket_name/g"
    sed "${sedi[@]}" -e $replace $file

    replace="s/%%DASHED_VERSION%%/$dashed_version/g"
    sed "${sedi[@]}" -e $replace $file

    # replace cdk-xxxxxxx-assets-* bucket with the assets bucket name
    replace="s/cdk-[a-z0-9]+-assets-\\$\{AWS::AccountId\}/$dist_bucket_name/g"
    sed "${sedi[@]}" -E $replace $file

    replace="s/cdk-[a-z0-9]+-assets-<AWS::AccountId>/$dist_bucket_name/g"
    sed "${sedi[@]}" -E $replace $file
done

echo "------------------------------------------------------------------------------"
echo "[Packing] Source code artifacts"
echo "------------------------------------------------------------------------------"
# ... For each asset.*.zip source code artifact in the temporary /staging folder...
cd $staging_dist_dir
for f in `find . -name "*.zip" -mindepth 1 -maxdepth 1 -type f`; do
    # Rename the artifact, removing the period for handler compatibility
    pfname="$(basename -- $f)"
    fname="$(echo $pfname | sed -e 's/asset\./asset/g')"
    mv $f $fname

    # Copy the artifact from /staging to /regional-s3-assets
    cp $fname $build_dist_dir
done

for d in `find . -mindepth 1 -maxdepth 1 -type d`; do
    # Rename the artifact, removing the period for handler compatibility
    pfname="$(basename -- $d)"
    fname="$(echo $pfname | sed -e 's/\.//g')"
    mv $d $fname

    # Zip artifacts from asset folder
    cd $fname
    zip -r ../$fname.zip * > /dev/null
    cd ..

    # Copy the zipped artifact from /staging to /regional-s3-assets
    cp $fname.zip $build_dist_dir

    # Remove the old artifacts from /staging
    rm -rf $fname
    rm $fname.zip
done

echo "------------------------------------------------------------------------------"
echo "[Cleanup] Remove temporary files"
echo "------------------------------------------------------------------------------"
cd $deployment_dir
rm -rf $staging_dist_dir

echo "------------------------------------------------------------------------------"
echo "[Info] Deployment Assets Created"
echo "------------------------------------------------------------------------------"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}If you have not previously created S3 buckets to upload assets to, then run: ${NC}"
echo -e "${GREEN}aws s3 mb s3://$template_bucket_name ${NC}"
echo -e "${GREEN}aws s3 mb s3://$dist_bucket_name ${NC}"

echo -e "${YELLOW}To upload the assets, run: ${NC}"
echo -e "${GREEN}aws s3 cp $template_dist_dir s3://$template_bucket_name/$solution_name/$solution_version/ --recursive ${NC}"
echo -e "${GREEN}aws s3 cp $build_dist_dir s3://$dist_bucket_name/$solution_name/$solution_version/ --recursive ${NC}"

# If getting called from CMS, copy assets to the cms assets dir
if [[ cms_deployment_dir != "" ]]; then
  cp $template_dist_dir/* $cms_deployment_dir/global-s3-assets 2>/dev/null || :
  cp $build_dist_dir/* $cms_deployment_dir/regional-s3-assets 2>/dev/null || :
fi
