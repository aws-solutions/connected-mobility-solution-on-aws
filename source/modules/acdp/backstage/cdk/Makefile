# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# AWS CONFIGURATION
# ========================================================
DEFAULTS.AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query "Account" --output text)
DEFAULTS.AWS_REGION := $(shell aws configure get region --output text)

export AWS_ACCOUNT_ID ?= ${DEFAULTS.AWS_ACCOUNT_ID}
export AWS_REGION ?= ${DEFAULTS.AWS_REGION}

# ========================================================
# SOLUTION METADATA
# ========================================================
export SOLUTION_NAME ?= connected-mobility-solution-on-aws
export SOLUTION_DESCRIPTION ?= Accelerate development and deployment of connected vehicle assets with purpose-built, deployment-ready accelerators, and an Automotive Cloud Developer Portal
export SOLUTION_VERSION ?= v1.1.3
export SOLUTION_AUTHOR = AWS Industrial Solutions Team
export SOLUTION_ID = SO0241
export APPLICATION_TYPE = AWS-Solutions

# ========================================================
# ENVIRONMENT CONFIGURATION
# ========================================================
DEFAULTS.NODE_VERSION := $(shell cat .nvmrc 2> /dev/null)
DEFAULTS.PYTHON_VERSION := $(shell cat .python-version)

export NODE_VERSION ?= ${DEFAULTS.NODE_VERSION}
export PYTHON_VERSION ?= ${DEFAULTS.PYTHON_VERSION}

export PYTHON_MINIMUM_VERSION_SUPPORTED = 3.10
export PIPENV_IGNORE_VIRTUALENVS = 1
export PIPENV_VENV_IN_PROJECT = 1
export LANG = en_US.UTF-8

# ========================================================
# VARIABLES
# ========================================================
export REGIONAL_ASSET_BUCKET_BASE_NAME ?= acdp-assets-${AWS_ACCOUNT_ID}
export REGIONAL_ASSET_BUCKET_NAME ?= ${REGIONAL_ASSET_BUCKET_BASE_NAME}-${AWS_REGION}
export GLOBAL_ASSET_BUCKET_NAME ?= ${REGIONAL_ASSET_BUCKET_NAME}

# Using a ?= here fails to update the variable when this file is imported from each module makefile during a makefile chain
export S3_ASSET_KEY_PREFIX = ${SOLUTION_NAME}/${SOLUTION_VERSION}/${MODULE_NAME}

# Used by CDK apps
export S3_ASSET_BUCKET_BASE_NAME ?= ${REGIONAL_ASSET_BUCKET_BASE_NAME}

# ==================================================================================
# PRINT COLORS
# 	To use, simply add ${<color>}<text> to get the colored text.
#   To disable color, add ${NC} at the point you'd like it to stop.
#   printf is recommended over echo if wanting color because of more multi-platform support.
#   https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
# ==================================================================================
export RED = \033[0;31m
export GREEN = \033[0;32m
export YELLOW = \033[0;33m
export BLUE = \033[0;34m
export MAGENTA = \033[0;35m
export CYAN = \033[0;36m
export NC = \033[00m


# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= acdp-backstage
export MODULE_SHORT_NAME ?= ${MODULE_NAME}
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= A CDK Python app to provision Spotify Backstage
export MODULE_AUTHOR ?= AWS Industrial Solutions Team
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

export GLOBAL_ASSET_BUCKET_REGION = $(shell BUCKET=${GLOBAL_ASSET_BUCKET_NAME} ${MODULE_PATH}/deployment/determine-bucket-region.sh)
export REGIONAL_ASSET_BUCKET_REGION = $(shell BUCKET=${REGIONAL_ASSET_BUCKET_NAME} ${MODULE_PATH}/deployment/determine-bucket-region.sh)

# ========================================================
# ENVIRONMENT CONFIGURATION
# ========================================================
export NODE_VERSION := $(shell cat .nvmrc)
export PIPENV_IGNORE_VIRTUALENVS = 1
export PIPENV_VENV_IN_PROJECT = 1
export PYTHON_VERSION := $(shell cat .python-version)
export PYTHON_MINIMUM_VERSION_SUPPORTED = 3.10

# ========================================================
# VARIABLES
# ========================================================

export ACDP_UNIQUE_ID ?= acdp

export STACK_NAME ?= ${ACDP_UNIQUE_ID}--${MODULE_NAME}
export STACK_TEMPLATE_NAME = ${MODULE_NAME}.template
export STACK_TEMPLATE_PATH ?= deployment/global-s3-assets/${MODULE_NAME}/${STACK_TEMPLATE_NAME}
export S3_ASSET_KEY_PREFIX ?= ${SOLUTION_NAME}/${SOLUTION_VERSION}/${MODULE_NAME}

export CAPABILITY_ID ?= CMS.6

export BACKSTAGE_IMAGE_TAG ?= latest

export ROUTE53_HOSTED_ZONE_NAME ?= $(shell aws ssm get-parameter --name /solution/${ACDP_UNIQUE_ID}/config/route53/zone-name --with-decryption --query "Parameter.Value" --output text 2> /dev/null)
export ROUTE53_BASE_DOMAIN ?= $(shell aws ssm get-parameter --name /solution/${ACDP_UNIQUE_ID}/config/route53/base-domain --with-decryption --query "Parameter.Value" --output text 2> /dev/null)

# Backstage is built directly via codepipeline,
# so use local asset bucket instead of public ones when running in this way.
export LOCAL_ASSET_BUCKET_NAME ?= ${REGIONAL_ASSET_BUCKET_BASE_NAME}-${AWS_REGION}
export GLOBAL_ASSET_BUCKET_NAME = ${LOCAL_ASSET_BUCKET_NAME}
export REGIONAL_ASSET_BUCKET_NAME = ${LOCAL_ASSET_BUCKET_NAME}


.PHONY: install
install: pipenv-install ## Installs the resources and dependencies required to build the solution.
	@printf "%bInstall finished.%b\n" "${GREEN}" "${NC}"

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
			${shell [ -n "${CLOUDFORMATION_ROLE_ARN}" ] && echo "--role-arn ${CLOUDFORMATION_ROLE_ARN}"}

.PHONY: destroy
destroy: destroy-stack ## Teardown deployed stack
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"

## ========================================================
## COMMON TARGETS
## ========================================================
.PHONY: pipenv-install
pipenv-install: ## Using pipenv, installs pip dependencies.
	@printf "%bInstalling pip dependencies: %s%b\n" "${MAGENTA}" "${MODULE_NAME}" "${NC}"
	@pipenv install --dev --python ${PYTHON_VERSION}
	@pipenv clean --python ${PYTHON_VERSION}

.PHONY: build
build: verify-required-tools ## Build templates and assets for the module.
	@printf "%bBuilding the module.%b\n" "${MAGENTA}" "${NC}"
	${MODULE_PATH}/deployment/build-s3-dist.sh

.PHONY: upload
upload: ## Upload templates and build assets for the module to S3 buckets.
	@printf "%bUploading S3 assets for the module.%b\n" "${MAGENTA}" "${NC}"
	${MODULE_PATH}/deployment/upload-s3-dist.sh

.PHONY: destroy-stack
destroy-stack: ## Delete the stack for the module.
	@printf "%bDelete the module deployment.%b\n" "${MAGENTA}" "${NC}"
	@aws cloudformation delete-stack --stack-name "${STACK_NAME}"
	@aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}"

.PHONY: all
all: build upload deploy ## Rebuild modules, upload assets to s3, and deploy

## ========================================================
## TESTING
## ========================================================
.PHONY: verify-module
verify-module: cfn-nag unit-tests ## Run all testing for the module.
	@printf "%bFinished testing.%b\n" "${MAGENTA}" "${NC}"

.PHONY: test
test: cfn-nag unit-tests ## Run all testing for the module.
	@printf "%bFinished testing.%b\n" "${MAGENTA}" "${NC}"

.PHONY: cfn-nag
cfn-nag: ## Run cfn-nag for the module.
	@printf "%bRunning cfn-nag checks.%b\n" "${MAGENTA}" "${NC}"
	-${MODULE_PATH}/deployment/run-cfn-nag.sh

.PHONY: unit-tests
unit-tests: ## Run unit-tests for the module.
	@printf "%bRunning unit tests.%b\n" "${MAGENTA}" "${NC}"
	-${MODULE_PATH}/deployment/run-unit-tests.sh

.PHONY: update-snapshots
update-snapshots: ## Update snapshot files for the module.
	@printf "%bUpdating unit test snapshots.%b\n" "${MAGENTA}" "${NC}"
	-${MODULE_PATH}/deployment/run-unit-tests.sh -r -s

## ========================================================
## HELP COMMANDS
## ========================================================
.PHONY: help
help: ## Displays this help message.
	@grep -E '^[a-zA-Z0-9 -]+:.*##|^##.*'  ${MODULE_PATH}/Makefile | while read -r l; \
	do ( [[ "$$l" =~ ^"##" ]] && printf "%b%s%b\n" "${MAGENTA}" "$$(echo $$l | cut -f 2- -d' ')" "${NC}") \
	|| ( printf "%b%-35s%s%b\n" "${GREEN}" "$$(echo $$l | cut -f 1 -d':')" "$$(echo $$l | cut -f 3- -d'#')" "${NC}"); \
	done;

.PHONY: print-module-name
print-module-name: ## Used to get module name safely from any directory if used with make -C
	@printf "${MODULE_NAME}"

.PHONY: version
version: ## Display module name and current version
	@printf "%b%35.35s%b version:%b%s%b\n" $$( [[ "${MODULE_PATH}" = *"lib"* ]] && echo "${YELLOW}" || echo "${CYAN}" ) "${MODULE_NAME}" "${NC}" "${GREEN}" "${MODULE_VERSION}" "${NC}"

.PHONY: verify-required-tools
verify-required-tools: ## Checks the environment for the required dependencies.
ifneq (v${NODE_VERSION}, $(shell node --version | cut -d "." -f 1-2))
	$(error Node version "v${NODE_VERSION}" is required, as specified in .nvmrc. "$(shell node --version | cut -d "." -f 1-2)" was found instead. Please install the correct version by running `nvm install`.)
endif
ifeq (, $(shell which npm))
	$(error Npm is required and should be automatically installed with node. Please check your node installation.`)
endif
ifeq (, $(shell which yarn))
	$(error Yarn is required, as specified in the README. Please see the following link for installation (OS specific): https://classic.yarnpkg.com/lang/en/docs/install/#mac-stable)
endif
ifneq (Python ${PYTHON_VERSION}, $(shell python --version | cut -d "." -f 1-2))
	$(error Python version "Python ${PYTHON_VERSION}" is required, as specified in .python-version. "$(shell python --version | cut -d "." -f 1-2)" was found instead. Please install the correct version by running `pyenv install -s`)
endif
ifeq (, $(shell which pipenv))
	$(error pipenv is required, as specified in the README. Please see the following link for installation: https://pipenv.pypa.io/en/latest/installation.html)
endif
ifeq (, $(shell which aws))
	$(error The aws CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
endif
ifeq (, $(shell which cdk))
	$(error The aws-cdk CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cdk/v2/guide/cli.html)
endif
	@printf "%bDependencies verified.%b\n" "${GREEN}" "${NC}"
