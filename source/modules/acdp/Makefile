# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= acdp
export MODULE_SHORT_NAME ?= ${MODULE_NAME}
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= Deployment solution using Spotify Backstage to deploy and manage CMS modules
export MODULE_AUTHOR ?= AWS Industrial Solutions Team

SOLUTION_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ========================================================
# VARIABLES
# ========================================================
export STACK_NAME ?= ${ACDP_UNIQUE_ID}--${MODULE_NAME}
export STACK_TEMPLATE_NAME = ${MODULE_NAME}.template
export STACK_TEMPLATE_PATH ?= deployment/global-s3-assets/${MODULE_NAME}/${STACK_TEMPLATE_NAME}

export CAPABILITY_ID ?= CMS.6

# Deploy variables not in .cmsrc
export ACDP_UNIQUE_ID ?= acdp
export BACKSTAGE_LOG_LEVEL ?= info
export BACKSTAGE_S3_DISCOVERY_REFRESH_MINS ?= 30

# Backstage Multi-Acct Setup Directory Inputs
export ENABLE_MULTI_ACCOUNT_DEPLOYMENT ?= false
export ORGS_MANAGEMENT_AWS_ACCOUNT_ID ?= null
export ORGS_MANAGEMENT_ACCOUNT_REGION ?= null

# Multi account guidance inputs
export TRANSFORM_STACK_NAME ?= OuArnListMacroStack
export ACDP_MULTI_ACCT_SETUP_STACK_NAME ?= AcdpMultiAcctStack

# NOTE:
# Assess whether this needs to be an environment variable. It's only read in the ACDP CDK, and shouldn't be customized. Can it be set in the CDK?
export BACKSTAGE_ASSETS_PREFIX ?= ${SOLUTION_NAME}/${SOLUTION_VERSION}/backstage

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

.PHONY: upgrade
upgrade: pipenv-lock ## Upgrades Pipfile.lock.
	@printf "%bPipfile.lock upgrade finished.%b\n" "${GREEN}" "${NC}"
	@printf "%bRun \"make install\" to install upgraded python dependencies.%b\n" "${CYAN}" "${NC}"

.PHONY: install
install: pipenv-sync cdk-solution-helper-clean-install ## Installs the resources and dependencies required to build the solution.
	@printf "%bInstall finished.%b\n" "${GREEN}" "${NC}"

.PHONY: deploy
deploy: verify-environment ## Deploy the stack for the module.
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
			"AdminUserEmail"="${ADMIN_USER_EMAIL}" \
			"ShouldCreateCognitoUser"="${SHOULD_CREATE_COGNITO_USER}" \
			"UseBackstageAuthRedirectFlow"="${USE_BACKSTAGE_AUTH_REDIRECT_FLOW}" \
			"BackstageAdditionalScopes"="${BACKSTAGE_ADDITIONAL_SCOPES}" \
			"FullyQualifiedDomainName"="${FULLY_QUALIFIED_DOMAIN_NAME}" \
			"Route53HostedZoneId"="${ROUTE53_HOSTED_ZONE_ID}" \
			"CustomAcmCertificateArn"="${CUSTOM_ACM_CERTIFICATE_ARN}" \
			"IsPublicFacing"="${IS_PUBLIC_FACING}" \
			"BackstageName"="${BACKSTAGE_NAME}" \
			"BackstageOrg"="${BACKSTAGE_ORG}" \
			"BackstageLogLevel"="${BACKSTAGE_LOG_LEVEL}" \
			"BackstageLocalAssetDiscoveryRefreshMins"="${BACKSTAGE_S3_DISCOVERY_REFRESH_MINS}" \
			"S3LogExpirationDays"="${LOG_BUCKET_RETENTION_DAYS}" \
			"EnableMultiAccountDeployment"="${ENABLE_MULTI_ACCOUNT_DEPLOYMENT}" \
			"OrgsManagementAwsAccountId"="${ORGS_MANAGEMENT_AWS_ACCOUNT_ID}" \
			"OrgsManagementAccountRegion"="${ORGS_MANAGEMENT_ACCOUNT_REGION}"

.PHONY: destroy-backstage
destroy-backstage: ## Delete the backstage stack and ecr repository
	@printf "%bCalling Backstage destroy target.%b\n" "${MAGENTA}" "${NC}"
	@cd "${MODULE_PATH}/../backstage" && make destroy
	@printf "%bBackstage destroy finished.%b\n" "${MAGENTA}" "${NC}"

.PHONY: destroy
destroy: destroy-backstage destroy-stack ## Delete the stack for the module.
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"

.PHONY: deploy-ou-arn-list-macro
deploy-ou-arn-list-macro: ## Deploy the OU Arn List Macro stack
	@printf "%bDeploy the multi account guidance macro stack.%b\n" "${MAGENTA}" "${NC}"
	aws cloudformation create-stack --stack-name ${TRANSFORM_STACK_NAME} \
        --template-body file://guidance/ou_arn_list_macro.template.yaml \
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND

	aws cloudformation wait stack-create-complete --stack-name "${TRANSFORM_STACK_NAME}"

.PHONY: destroy-ou-arn-list-macro
destroy-ou-arn-list-macro: ## Delete the OU Arn List Macro stack
	@printf "%Destroy the multi account guidance macro stack.%b\n" "${MAGENTA}" "${NC}"
	aws cloudformation delete-stack --stack-name "${TRANSFORM_STACK_NAME}"

	aws cloudformation wait stack-delete-complete --stack-name "${TRANSFORM_STACK_NAME}"

.PHONY: deploy-multi-account-guidance
deploy-multi-account-guidance: ## Deploy the Multi Account Setup stack
	@printf "%bDeploy the multi account guidance stack.%b\n" "${MAGENTA}" "${NC}"
	aws cloudformation create-stack --stack-name ${ACDP_MULTI_ACCT_SETUP_STACK_NAME} \
        --template-body file://guidance/acdp_multi_acct_setup.template.yaml \
        --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
        --parameters \
            ParameterKey=AcdpAwsAccountId,ParameterValue=${ACDP_AWS_ACCOUNT_ID} \
            ParameterKey=AcdpUniqueId,ParameterValue=${ACDP_UNIQUE_ID} \
            ParameterKey=AcdpDeploymentRegion,ParameterValue=${ACDP_DEPLOYMENT_REGION} \
            ParameterKey=OrgId,ParameterValue=${ORG_ID} \
            ParameterKey=OuIdList,ParameterValue=\"${OU_ID_LIST}\" \
            ParameterKey=AllowedRegions,ParameterValue=\"${ALLOWED_REGIONS}\" \
            ParameterKey=PrivateAssetsBucketName,ParameterValue=${PRIVATE_ASSETS_BUCKET_NAME}

	aws cloudformation wait stack-create-complete --stack-name "${ACDP_MULTI_ACCT_SETUP_STACK_NAME}"

.PHONY: destroy-multi-account-guidance
destroy-multi-account-guidance: ## Delete the Multi Account Setup stack
	@printf "%Destroy the multi account guidance stack.%b\n" "${MAGENTA}" "${NC}"
	aws cloudformation delete-stack --stack-name "${ACDP_MULTI_ACCT_SETUP_STACK_NAME}"

	aws cloudformation wait stack-delete-complete --stack-name "${ACDP_MULTI_ACCT_SETUP_STACK_NAME}"

## ========================================================
## UTILITY
## ========================================================
.PHONY: verify-environment
verify-environment: ## Checks the cdk environment for the required environment variables, as set via .cmsrc or manual export.
ifneq (, $(wildcard ./cdk.context.json))
	$(error 'cdk.context.json' cannot exist. Please delete the file and try again)
endif
ifndef ADMIN_USER_EMAIL
	$(error ADMIN_USER_EMAIL is undefined. Set the variable using `export ADMIN_USER_EMAIL=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef SHOULD_CREATE_COGNITO_USER
	$(error SHOULD_CREATE_COGNITO_USER is undefined. Set the variable using `export SHOULD_CREATE_COGNITO_USER=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef FULLY_QUALIFIED_DOMAIN_NAME
	$(error FULLY_QUALIFIED_DOMAIN_NAME is undefined. Set the variable using `export FULLY_QUALIFIED_DOMAIN_NAME=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef IS_PUBLIC_FACING
	$(error IS_PUBLIC_FACING is undefined. Set the variable using `export IS_PUBLIC_FACING=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef VPC_NAME
	$(error VPC_NAME is undefined. Set the variable using `export VPC_NAME=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef IDENTITY_PROVIDER_ID
	$(error IDENTITY_PROVIDER_ID is undefined. Set the variable using `export IDENTITY_PROVIDER_ID=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef USE_BACKSTAGE_AUTH_REDIRECT_FLOW
	$(error USE_BACKSTAGE_AUTH_REDIRECT_FLOW is undefined. Set the variable using `export USE_BACKSTAGE_AUTH_REDIRECT_FLOW=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef BACKSTAGE_NAME
	$(error BACKSTAGE_NAME is undefined. Set the variable using `export BACKSTAGE_NAME=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef BACKSTAGE_ORG
	$(error BACKSTAGE_ORG is undefined. Set the variable using `export BACKSTAGE_ORG=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
ifndef ENABLE_MULTI_ACCOUNT_DEPLOYMENT
	$(error ENABLE_MULTI_ACCOUNT_DEPLOYMENT is undefined. Set the variable using `export ENABLE_MULTI_ACCOUNT_DEPLOYMENT=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
endif
	@printf "%bEnvironment variables verified.%b\n" "${GREEN}" "${NC}"
