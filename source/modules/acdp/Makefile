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
export ACDP_UNIQUE_ID ?= acdp

export STACK_NAME ?= ${ACDP_UNIQUE_ID}--${MODULE_NAME}
export STACK_TEMPLATE_NAME = ${MODULE_NAME}.template
export STACK_TEMPLATE_PATH ?= deployment/global-s3-assets/${MODULE_NAME}/${STACK_TEMPLATE_NAME}

export CAPABILITY_ID ?= CMS.6

export BACKSTAGE_ASSETS_PREFIX ?= ${SOLUTION_NAME}/${SOLUTION_VERSION}/backstage
export BACKSTAGE_LOG_LEVEL ?= info
export BACKSTAGE_S3_DISCOVERY_REFRESH_MINS ?= 30
export BACKSTAGE_NAME ?= DEFAULT_NAME
export BACKSTAGE_ORG ?= DEFAULT_ORG

export ROUTE53_BASE_DOMAIN ?= ${ROUTE53_ZONE_NAME}

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

## ========================================================
## INSTALL
## ========================================================
.PHONY: yarn-install
yarn-install: ## Using yarn, installs node dependencies for all modules.
	@printf "%bInstalling node dependencies using yarn.%b\n" "${MAGENTA}" "${NC}"
	cd backstage && yarn install

.PHONY: install
install: pipenv-install yarn-install ## Installs the resources and dependencies required to build the solution.
	@printf "%bInstall finished.%b\n" "${GREEN}" "${NC}"

## ========================================================
## BUILD AND DEPLOY
## ========================================================
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
			"UserEmail"="${USER_EMAIL}" \
			"Route53ZoneName"="${ROUTE53_ZONE_NAME}" \
			"Route53BaseDomain"="${ROUTE53_BASE_DOMAIN}" \
			"BackstageName"="${BACKSTAGE_NAME}" \
			"BackstageOrg"="${BACKSTAGE_ORG}" \
			"BackstageLogLevel"="${BACKSTAGE_LOG_LEVEL}" \
			"BackstageLocalAssetDiscoveryRefreshMins"="${BACKSTAGE_S3_DISCOVERY_REFRESH_MINS}" \
			"VpcName"="${VPC_NAME}" \

.PHONY: destroy-ecr
destroy-ecr: ## Destroy the ECR images since CloudFormation cannot.
	@printf "%bDelete the ECR repository.%b\n" "${MAGENTA}" "${NC}"
	aws ecr delete-repository --repository-name "${ACDP_UNIQUE_ID}-backstage" --force || true

.PHONY: destroy
destroy: destroy-ecr destroy-stack ## Delete the stack for the module.
	@printf "%bDelete the module deployment.%b\n" "${MAGENTA}" "${NC}"
	aws ecr delete-repository --repository-name "${ACDP_UNIQUE_ID}-backstage" --force || true
	aws cloudformation delete-stack \
		--stack-name ${STACK_NAME} \

## ========================================================
## LOCAL UTILITY
## ========================================================

.PHONY: run-backstage-local
run-backstage-local: run-postgres-local ## Start a local instance of Backstage
	cd backstage && yarn run dev

.PHONY: run-backstage-backend-local
run-backstage-backend-local: run-postgres-local ## Start a local instance of Backstage's backend
	cd backstage && yarn run start-backend

.PHONY: run-backstage-frontend-local
run-backstage-frontend-local: ## Start a local instance of Backstage's frontend
	cd backstage && yarn start

.PHONY: run-postgres-local
run-postgres-local: ## Start a local instance of postgres for use with Backstage
	cd backstage && docker-compose up &> ./docker_postgres.log &

.PHONY: stop-backstage-local
stop-backstage-local:
	cd backstage && docker-compose stop && rm -f ./docker_postgres.log

## ========================================================
## UTILITY
## ========================================================
.PHONY: verify-environment
verify-environment: ## Checks the cdk environment for the required environment variables.
ifneq (, $(wildcard ./cdk.context.json))
	$(error 'cdk.context.json' cannot exist. Please delete the file and try again)
endif
ifndef VPC_NAME
	$(error VPC_NAME is undefined. Set the variable using `export VPC_NAME=...`, or run `source .cmsrc`)
endif
ifndef USER_EMAIL
	$(error USER_EMAIL is undefined. Set the variable using `export USER_EMAIL=...`, or run `source .cmsrc`)
endif
ifndef ROUTE53_ZONE_NAME
	$(error ROUTE53_ZONE_NAME is undefined. Set the variable using `export ROUTE53_ZONE_NAME=...`, or run `source .cmsrc`)
endif
	@printf "%bEnvironment variables verified.%b\n" "${GREEN}" "${NC}"
