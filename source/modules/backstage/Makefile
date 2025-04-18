# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= backstage
export MODULE_SHORT_NAME ?= ${MODULE_NAME}
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= Backstage assets for use with the ACDP Pipeline
export MODULE_AUTHOR ?= AWS Industrial Solutions Team

SOLUTION_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ========================================================
# VARIABLES
# ========================================================
export ACDP_UNIQUE_ID ?= acdp

# Multi Acct Variables for Local Development
export ORGS_ACCOUNT_DIRECTORY_ASSUME_ROLE_NAME ?= acdp-orgs-trust-role
export ORGS_AVAILABLE_REGIONS_SSM_PARAMETER_NAME ?= /solution/acdp/multi-acct-setup/available-regions
export ORGS_ENROLLED_ORGS_SSM_PARAMETER_NAME ?= /solution/acdp/multi-acct-setup/enrolled-organizations
export METRICS_ROLE_NAME ?= acdp-metrics-role

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

.PHONY: yarn-install
yarn-install: ## Using yarn, installs node dependencies from yarn.lock.
	@printf "%bInstalling node dependencies from yarn.lock.%b\n" "${MAGENTA}" "${NC}"
	@yarn install --immutable --refresh-lockfile

.PHONY: yarn-up
yarn-up: ## Checks for node dependency updates and upgrades yarn.lock.
	@printf "%bUpgrading yarn.lock dependencies.%b\n" "${MAGENTA}" "${NC}"
	@yarn up --mode=update-lockfile

.PHONY: upgrade
upgrade: pipenv-lock yarn-up ## Checks for dependency upgrades and updates lock files. Does not install upgraded dependencies.
	@printf "%bUpgrading Backstage CDK pip dependencies.%b\n" "${MAGENTA}" "${NC}"
	@cd "${MODULE_PATH}/cdk" && make upgrade
	@printf "%bFinished updating lock files.%b\n" "${GREEN}" "${NC}"
	@printf "%bRun \"make install\" to install upgraded dependencies.%b\n" "${CYAN}" "${NC}"

.PHONY: install
install: pipenv-sync yarn-install ## Installs the resources and dependencies required to build the solution.
	@printf "%bInstall finished.%b\n" "${GREEN}" "${NC}"

.PHONY: deploy
deploy: ## Deploy the stack for the module.
	@printf "%bCopying ACDP assets to S3.\n%b" "${MAGENTA}" "${NC}"
	@ACDP_ASSET_BUCKET=$$(aws ssm get-parameter --name /solution/${ACDP_UNIQUE_ID}/config/acdp-asset-config/local/asset-bucket/name --with-decryption --query "Parameter.Value" --output text 2> /dev/null); \
	S3_PATH="s3://$${ACDP_ASSET_BUCKET}/${S3_ASSET_KEY_PREFIX}"; \
	aws s3 cp --recursive ${MODULE_PATH}/deployment/regional-s3-assets/${MODULE_NAME}/ $${S3_PATH}; \
	printf "%bCopied assets to %s\n%b" "${GREEN}" "$${S3_PATH}" "${NC}"

	@printf "%bBeginning Backstage pipeline execution.\n%b" "${MAGENTA}" "${NC}"
	@ACDP_BACKSTAGE_PIPELINE_NAME=$$(aws ssm get-parameter --name /solution/${ACDP_UNIQUE_ID}/config/codepipeline-project/name --with-decryption --query "Parameter.Value" --output text 2> /dev/null); \
	aws codepipeline start-pipeline-execution --name $${ACDP_BACKSTAGE_PIPELINE_NAME}; \
	printf "%bStarted Pipeline: %s\n%b" "${GREEN}" "$${ACDP_BACKSTAGE_PIPELINE_NAME}" "${NC}"

.PHONY: destroy-ecr
destroy-ecr: ## Destroy the ECR images since CloudFormation cannot.
	@printf "%bDeleting the ECR repository.%b\n" "${MAGENTA}" "${NC}"
	aws ecr delete-repository --repository-name "${ACDP_UNIQUE_ID}-backstage" --force || true
	@printf "%bECR repository deleted.%b\n" "${GREEN}" "${NC}"

.PHONY: destroy
destroy: destroy-ecr ## Delete the backstage stack.
	@printf "%bDeleting the backstage deployment.%b\n" "${MAGENTA}" "${NC}"
	aws cloudformation delete-stack --stack-name "${ACDP_UNIQUE_ID}--acdp-backstage"
	aws cloudformation wait stack-delete-complete --stack-name "${ACDP_UNIQUE_ID}--acdp-backstage" || true
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"

## ========================================================
## LOCAL UTILITY
## ========================================================
.PHONY: run-backstage-local
run-backstage-local: run-postgres-local ## Start a local instance of Backstage
	yarn run dev

.PHONY: run-backstage-backend-local
run-backstage-backend-local: run-postgres-local ## Start a local instance of Backstage's backend
	yarn run start-backend

.PHONY: run-backstage-frontend-local
run-backstage-frontend-local: ## Start a local instance of Backstage's frontend
	yarn start

.PHONY: run-postgres-local
run-postgres-local: ## Start a local instance of postgres for use with Backstage
	@finch compose -f ./finch-compose.yaml up &> ./finch_postgres.log &
	@RETRIES=3; \
	for i in $$(seq 1 $$RETRIES); do \
		echo "Attempt $$i: Checking if 'backstage-local-db' container is running..."; \
		STATUS=$$(finch inspect --format='{{.State.Running}}' backstage-local-db 2>/dev/null); \
		if [ "$$STATUS" == "true" ]; then \
			echo "'backstage-local-db' is up and running." && break; \
		elif [ $$i -lt $$RETRIES ]; then \
			echo "Container not running. Retrying in 5 seconds..." &&	sleep 5; \
		else \
			echo "Error: Container 'backstage-local-db' is not running or does not exist after $$RETRIES attempts." &&	exit 1; \
		fi; \
	done

.PHONY: stop-backstage-local
stop-backstage-local: ## Stop the Backstage local docker instance
	finch compose stop && rm -f ./finch_postgres.log
