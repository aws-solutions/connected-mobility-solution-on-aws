# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= acdp-backstage
export MODULE_SHORT_NAME ?= ${MODULE_NAME}
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= A CDK Python app to provision Spotify Backstage
export MODULE_AUTHOR ?= AWS Industrial Solutions Team

SOLUTION_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../../..)
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ========================================================
# VARIABLES
# ========================================================

export ACDP_UNIQUE_ID ?= acdp
export STACK_NAME ?= ${ACDP_UNIQUE_ID}--${MODULE_NAME}
export STACK_TEMPLATE_NAME = ${MODULE_NAME}.template
export STACK_TEMPLATE_PATH ?= deployment/global-s3-assets/${MODULE_NAME}/${STACK_TEMPLATE_NAME}

export CAPABILITY_ID ?= CMS.6
export BACKSTAGE_IMAGE_TAG ?= latest

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

# Backstage is built directly via codepipeline,
# so use local asset bucket instead of public ones when running in this way.
export LOCAL_ASSET_BUCKET_NAME ?= ${REGIONAL_ASSET_BUCKET_BASE_NAME}-${AWS_REGION}
export GLOBAL_ASSET_BUCKET_NAME = ${LOCAL_ASSET_BUCKET_NAME}
export REGIONAL_ASSET_BUCKET_NAME = ${LOCAL_ASSET_BUCKET_NAME}

export IS_PUBLIC_FACING ?= true

## ========================================================
## INSTALL
## ========================================================

.PHONY: install
install: pipenv-install cdk-solution-helper-install ## Installs the resources and dependencies required to build the solution.
	@printf "%bInstall finished.%b\n" "${GREEN}" "${NC}"

## ========================================================
## BUILD AND DEPLOY
## ========================================================

.PHONY: upload-local-assets
upload-local-assets: ## Upload templates and build assets for the module to S3 buckets.
	@printf "%bUploading S3 assets for the module.%b\n" "${MAGENTA}" "${NC}"
	pipenv run ${MODULE_PATH}/deployment/upload-s3-dist.sh

.PHONY: deploy
deploy: ## Deploy the stack for the module.
	@printf "%bDeploy the module.%b\n" "${MAGENTA}" "${NC}"
	aws cloudformation deploy \
		--stack-name ${STACK_NAME} \
		--template-file ${STACK_TEMPLATE_PATH} \
		--s3-bucket ${GLOBAL_ASSET_BUCKET_NAME} \
		--s3-prefix ${SOLUTION_NAME}/local/${MODULE_NAME} \
		--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
		--parameter-overrides \
			"AcdpUniqueId"="${ACDP_UNIQUE_ID}" \
			"VpcName"="${VPC_NAME}" \
			"IdentityProviderId"="${IDENTITY_PROVIDER_ID}" \
			"Route53HostedZoneId"="${ROUTE53_HOSTED_ZONE_ID}" \
			"FullyQualifiedDomainName"="${FULLY_QUALIFIED_DOMAIN_NAME}" \
			"CustomAcmCertificateArn"="${CUSTOM_ACM_CERTIFICATE_ARN}" \
			"IsPublicFacing"="${IS_PUBLIC_FACING}" \
			${shell [ -n "${CLOUDFORMATION_ROLE_ARN}" ] && echo "--role-arn ${CLOUDFORMATION_ROLE_ARN}"}

.PHONY: destroy
destroy: destroy-stack ## Teardown deployed stack
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"
