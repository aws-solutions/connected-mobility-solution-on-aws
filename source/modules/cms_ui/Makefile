# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

.DEFAULT_GOAL := help

# ========================================================
# SOLUTION METADATA
# ========================================================
export MODULE_NAME ?= cms-ui
export MODULE_SHORT_NAME ?= ui
export MODULE_VERSION ?= ${SOLUTION_VERSION}
export MODULE_DESCRIPTION ?= A CDK Python app containing the CMS UI
export MODULE_AUTHOR ?= AWS Industrial Solutions Team

SOLUTION_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../..)
MODULE_PATH := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# ========================================================
# VARIABLES
# ========================================================

export APP_UNIQUE_ID ?= cms
export STACK_NAME ?= ${APP_UNIQUE_ID}-app--${MODULE_NAME}
export STACK_TEMPLATE_NAME = ${MODULE_NAME}.template
export STACK_TEMPLATE_PATH ?= deployment/global-s3-assets/${MODULE_NAME}/${STACK_TEMPLATE_NAME}
export IS_DEMO_MODE ?= false

export CAPABILITY_ID ?= CMS.25

include ${SOLUTION_PATH}/makefiles/common_config.mk
include ${SOLUTION_PATH}/makefiles/global_targets.mk
include ${SOLUTION_PATH}/makefiles/module_targets.mk

RUNTIME_CONFIG_LOCAL_PATH := ./source/frontend/public/runtimeConfig.json

.PHONY: yarn-install
yarn-install: ## Using yarn, installs node dependencies from yarn.lock.
	@printf "%bInstalling node dependencies from yarn.lock.%b\n" "${MAGENTA}" "${NC}"
	@yarn --cwd "${MODULE_PATH}/source/frontend" install --immutable --refresh-lockfile
	@yarn --cwd "${MODULE_PATH}/source/handlers/fleet_management" install --immutable --refresh-lockfile

.PHONY: yarn-up
yarn-up: ## Checks for node dependency updates and upgrades yarn.lock without installing upgraded dependencies.
	@printf "%bUpgrading yarn.lock.%b\n" "${MAGENTA}" "${NC}"
	@yarn --cwd "${MODULE_PATH}/source/frontend" up --mode=update-lockfile
	@yarn --cwd "${MODULE_PATH}/source/handlers/fleet_management" up --mode=update-lockfile

.PHONY: upgrade
upgrade: pipenv-lock yarn-up ## Checks for dependency upgrades and updates lock files. Does not install upgraded dependencies.
	@printf "%bFinished updating lock files.%b\n" "${GREEN}" "${NC}"
	@printf "%bRun \"make install\" to install upgraded dependencies.%b\n" "${CYAN}" "${NC}"

.PHONY: install
install: pipenv-sync cdk-solution-helper-clean-install yarn-install ## Installs the resources and dependencies required to build the solution.
	@printf "%bInstall finished.%b\n" "${GREEN}" "${NC}"

.PHONY: deploy
deploy: ## Deploy the stack for the module.
	@printf "${MAGENTA}Deploy the module.${NC}\n"
	aws cloudformation deploy \
		--stack-name ${STACK_NAME} \
		--template-file ${STACK_TEMPLATE_PATH} \
		--s3-bucket ${GLOBAL_ASSET_BUCKET_NAME} \
		--s3-prefix ${SOLUTION_NAME}/local/${MODULE_NAME} \
		--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
		--parameter-overrides \
			"AppUniqueId"="${APP_UNIQUE_ID}" \
			"S3LogExpirationDays"="${LOG_BUCKET_RETENTION_DAYS}" \
			"IsDemoMode"="${IS_DEMO_MODE}" \

.PHONY: destroy
destroy: destroy-stack ## Teardown deployed stack
	@printf "%bDestroy finished.%b\n" "${GREEN}" "${NC}"


.PHONY: copy-runtime-config
copy-runtime-config:
	@printf "${MAGENTA}Fetching runtime config from SSM and copying to local.${NC}\n"
	$(eval S3_CONFIG_PATH := $(shell aws ssm get-parameter --name "/solution/${APP_UNIQUE_ID}/${MODULE_SHORT_NAME}/deployment/config-path" --query "Parameter.Value" --output text))
	@echo "SSM Parameter Retrieved: $(S3_CONFIG_PATH)"
	@if [ -z "$(S3_CONFIG_PATH)" ]; then \
		echo "Error: Config path SSM parameter not found."; \
		exit 1; \
	fi
	@echo "Downloading "$(S3_CONFIG_PATH)" to ${RUNTIME_CONFIG_LOCAL_PATH}..."
	aws s3 cp "$(S3_CONFIG_PATH)" "${RUNTIME_CONFIG_LOCAL_PATH}"
	jq '.' ${RUNTIME_CONFIG_LOCAL_PATH} | tee ${RUNTIME_CONFIG_LOCAL_PATH} > /dev/null
	@printf "Runtime config copied successfully."

.PHONY: add-localhost-callback-uri
add-localhost-callback-uri: ## Add localhost to callback URIs in the UI app client
	@printf "${MAGENTA}Fetching user pool ID and UI app client ID from SSM.${NC}\n"
	$(eval USER_POOL_ID := $(shell aws ssm get-parameter --name "/solution/auth/${APP_UNIQUE_ID}/user-pool/id" --query "Parameter.Value" --output text))
	$(eval USER_APP_CLIENT_ID := $(shell aws ssm get-parameter --name "/solution/${APP_UNIQUE_ID}/${MODULE_SHORT_NAME}/auth-app-client/id" --query "Parameter.Value" --output text))
	@printf "${MAGENTA}SSM Parameters Retrieved.${NC}\n"
	@if [[ -z "$(USER_POOL_ID)" || -z "${USER_APP_CLIENT_ID}" ]]; then \
		echo "Error: SSM parameter not found."; \
		exit 1; \
	fi
	$(eval CLIENT_CONFIG := $(shell aws cognito-idp describe-user-pool-client \
		--user-pool-id $(USER_POOL_ID) \
		--client-id $(USER_APP_CLIENT_ID) \
		--query 'UserPoolClient'))
	$(eval UPDATED_CALLBACKS := $(shell echo '$(CLIENT_CONFIG)' | jq '.CallbackURLs + ["http://localhost:5177", "http://localhost:5177/callback"]'))
	@printf "${MAGENTA}Updating app client configuration...${NC}\n"
	@aws cognito-idp update-user-pool-client \
		--user-pool-id $(USER_POOL_ID) \
		--client-id $(USER_APP_CLIENT_ID) \
		--client-name "$(shell echo '$(CLIENT_CONFIG)' | jq -r '.ClientName')" \
		--refresh-token-validity $(shell echo '$(CLIENT_CONFIG)' | jq -r '.RefreshTokenValidity') \
		--access-token-validity $(shell echo '$(CLIENT_CONFIG)' | jq -r '.AccessTokenValidity') \
		--id-token-validity $(shell echo '$(CLIENT_CONFIG)' | jq -r '.IdTokenValidity') \
		--token-validity-units '$(shell echo '$(CLIENT_CONFIG)' | jq -r '.TokenValidityUnits')' \
		--supported-identity-providers '$(shell echo '$(CLIENT_CONFIG)' | jq -r '.SupportedIdentityProviders')' \
		--callback-urls '$(UPDATED_CALLBACKS)' \
		--logout-urls '$(shell echo '$(CLIENT_CONFIG)' | jq -r '.LogoutURLs // []')' \
		--allowed-o-auth-flows '$(shell echo '$(CLIENT_CONFIG)' | jq -r '.AllowedOAuthFlows')' \
		--allowed-o-auth-scopes '$(shell echo '$(CLIENT_CONFIG)' | jq -r '.AllowedOAuthScopes')' \
		--prevent-user-existence-errors $(shell echo '$(CLIENT_CONFIG)' | jq -r '.PreventUserExistenceErrors') \
		--auth-session-validity $(shell echo '$(CLIENT_CONFIG)' | jq -r '.AuthSessionValidity') \
		$(shell if echo '$(CLIENT_CONFIG)' | jq -r '.EnableTokenRevocation' | grep -q true; then echo '--enable-token-revocation'; else echo '--no-enable-token-revocation'; fi) \
		$(shell if echo '$(CLIENT_CONFIG)' | jq -r '.AllowedOAuthFlowsUserPoolClient' | grep -q true; then echo '--allowed-o-auth-flows-user-pool-client'; else echo '--no-allowed-o-auth-flows-user-pool-client'; fi) \
		$(shell if echo '$(CLIENT_CONFIG)' | jq -r '.EnablePropagateAdditionalUserContextData' | grep -q true; then echo '--enable-propagate-additional-user-context-data'; else echo '--no-enable-propagate-additional-user-context-data'; fi)
	@printf "%bFinished adding localhost to the CMS UI user app client.%b\n" "${GREEN}" "${NC}"


.PHONY: run-frontend-local
run-frontend-local: ## Start a local instance of CMS UI frontend
	yarn --cwd "./source/frontend/" start
