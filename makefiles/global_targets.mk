.PHONY: create-upload-bucket
create-upload-bucket: ## Creates required bucket(s) for uploading assets to S3 to deploy CMS modules via Backstage.
ifeq (, $(shell which aws))
	$(error The aws CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
endif
	@printf "%bCreating required buckets...%b\n" "${MAGENTA}" "${NC}"
	@aws s3 mb "s3://${GLOBAL_ASSET_BUCKET_NAME}" 2>/dev/null || true
	@aws s3api put-bucket-versioning --bucket "${REGIONAL_ASSET_BUCKET_NAME}" --versioning-configuration Status=Enabled
	@aws s3api put-bucket-policy --bucket ${GLOBAL_ASSET_BUCKET_NAME} --policy '{"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Principal": {"AWS": "*"}, "Action": "s3:*", "Resource": ["arn:aws:s3:::${GLOBAL_ASSET_BUCKET_NAME}", "arn:aws:s3:::${GLOBAL_ASSET_BUCKET_NAME}/*"], "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}'
	@printf "%bBucket (%s) ready.%b\n" "${GREEN}" "${GLOBAL_ASSET_BUCKET_NAME}" "${NC}"
	@aws s3 mb "s3://${REGIONAL_ASSET_BUCKET_NAME}" 2>/dev/null || true
	@aws s3api put-bucket-versioning --bucket "${REGIONAL_ASSET_BUCKET_NAME}" --versioning-configuration Status=Enabled
	@aws s3api put-bucket-policy --bucket ${REGIONAL_ASSET_BUCKET_NAME} --policy '{"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Principal": {"AWS": "*"}, "Action": "s3:*", "Resource": ["arn:aws:s3:::${REGIONAL_ASSET_BUCKET_NAME}", "arn:aws:s3:::${REGIONAL_ASSET_BUCKET_NAME}/*"], "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]}'
	@printf "%bBucket (%s) ready.%b\n" "${GREEN}" "${REGIONAL_ASSET_BUCKET_NAME}" "${NC}"

.PHONY: build-python-package
build-python-package: ## Wraps normal setup.py commands to leverage the environment variables defined in Makefiles
	@pipenv run python setup.py build

.PHONY: install-python-package
install-python-package: ## Wraps normal setup.py commands to leverage the environment variables defined in Makefiles
	@pipenv run python setup.py install

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
