# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

unquote = $(patsubst "%,%,$(patsubst %",%,$(1)))

.DEFAULT_GOAL := help

# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= auth-setup
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= A CDK Python app for deploying a customizable but structured OAuth configuration, with optional Cognito infrastructure to populate this configuration.
export MODULE_AUTHOR ?= AWS Industrial Solutions Team

SOLUTION_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ========================================================
# VARIABLES
# ========================================================
export STACK_NAME ?= ${IDENTITY_PROVIDER_ID}-${MODULE_NAME}
export STACK_TEMPLATE_NAME = ${MODULE_NAME}.template
export STACK_TEMPLATE_PATH ?= deployment/global-s3-assets/${MODULE_NAME}/${STACK_TEMPLATE_NAME}

export CAPABILITY_ID ?= CMS.24

# Default Callback URI necessary for use with Backstage. Added by default to Cognito User app client.
ifdef FULLY_QUALIFIED_DOMAIN_NAME
	export CALLBACK_URLS ?= https://${FULLY_QUALIFIED_DOMAIN_NAME}/api/auth/oauth2/handler/frame
else
	export CALLBACK_URLS ?= https://example.com
endif

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

.PHONY: install
install: pipenv-install cdk-solution-helper-install ## Installs the resources and dependencies required to build the solution.
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
			"ShouldCreateCognitoResources"="${SHOULD_CREATE_COGNITO_RESOURCES}" \
 			"IdentityProviderId"="${IDENTITY_PROVIDER_ID}" \
			"CallbackUrls"="${CALLBACK_URLS}" \

.PHONY: destroy
destroy: destroy-stack ## Teardown deployed stack
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"

## ========================================================
## UTILITY
## ========================================================
.PHONY: verify-environment
verify-environment: ## Checks the cdk environment for the required environment variables, as set via .cmsrc or manual export.
ifneq (, $(wildcard ./cdk.context.json))
	$(error 'cdk.context.json' cannot exist. Please delete the file and try again)
endif
ifndef IDENTITY_PROVIDER_ID
	$(error IDENTITY_PROVIDER_ID is undefined. Set the variable using `export IDENTITY_PROVIDER_ID=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
ifndef SHOULD_CREATE_COGNITO_RESOURCES
	$(error SHOULD_CREATE_COGNITO_RESOURCES is undefined. Set the variable using `export SHOULD_CREATE_COGNITO_RESOURCES=...`, run `source .cmsrc` if it exists, or run `make create-rc-file` to generate .cmsrc)
endif
