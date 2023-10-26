#!/bin/bash
#
# Run this script to create IoT credentials required to deploy the Cms-provisioning-on-aws package.
# This script should be run from the project's root directory.
# Usage: ./deployment/create_iot_credentials.sh

project_root_dir="$PWD"
build_dir="$project_root_dir/build"
keys_and_cert_dir="$build_dir/credentials"

mkdir -p $keys_and_cert_dir

echo "------------------------------------------------------------------------------"
echo "Creating IoT keys and certificates"
echo "------------------------------------------------------------------------------"

certificate_file="$keys_and_cert_dir/simulator_claim_cert.pem"
public_key_file="$keys_and_cert_dir/simulator.public.key"
private_key_file="$keys_and_cert_dir/simulator.private.key"

if [ -f "$certificate_file" ] && [ -f "$public_key_file" ] && [ -f "$private_key_file" ]; then
    echo "Existing IoT credentials found in $keys_and_cert_dir. Skipping creating credentials!"
else
    echo "Did not find existing IoT credentials. Creating new credentials ..."
    certificate_id=$(aws iot create-keys-and-certificate \
        --no-set-as-active \
        --certificate-pem-outfile $certificate_file \
        --public-key-outfile $public_key_file \
        --private-key-outfile $private_key_file \
        | jq -r '.certificateId')

    # Delete the created certificate from IoT Core. Deployment
    # will fail if the certificate already exists in IoT Core.
    aws iot delete-certificate --certificate-id $certificate_id
fi

# Copy the certificate to the project root so it can be accessed by the stack
cp $certificate_file $project_root_dir

echo $'\nDone!'
