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
	@[ "v${NODE_VERSION}" = "$$(node --version | cut -d "." -f 1-2)" ] || ( printf "%bNode version %s is required, as specified in .nvmrc. %s was found instead. Please install the correct version by running 'nvm install'.%b\n" "${RED}" "v${NODE_VERSION}" "$(shell node --version | cut -d "." -f 1-2)" "${NC}"; sh -c 'exit 1' )
	@[ $$(which npm) ] || ( printf "%bNpm is required and should be automatically installed with node. Please check your node installation. (https://www.npmjs.com/) %b\n" "${RED}" "${NC}"; sh -c 'exit 1' )
	@[ $$(which yarn) ] || ( printf "%bYarn is required, as specified in the README. Please see the following link for installation (OS specific): https://classic.yarnpkg.com/lang/en/docs/install/#mac-stable%b\n" "${RED}" "${NC}"; sh -c 'exit 1' )
	@[ "Python ${PYTHON_VERSION}" = "$$(python --version | cut -d "." -f 1-2)" ] || ( printf "%bPython version %s is required, as specified in .python-version. %s was found instead. Please install the correct version by running 'pyenv install -s'%b\n" "${RED}" "Python ${PYTHON_VERSION}" "$(shell python --version | cut -d "." -f 1-2)" "${NC}"; sh -c 'exit 1' )
	@[ $$(which pipenv) ] || ( printf "%bpipenv is required, as specified in the README. Please see the following link for installation: https://pipenv.pypa.io/en/latest/installation.html%b\n" "${RED}" "${NC}"; sh -c 'exit 1' )
	@[ $$(which aws) ] || ( printf "%bThe aws CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html%b\n" "${RED}" "${NC}"; sh -c 'exit 1' )
	@[ $$(which cdk) ] || ( printf "%bThe aws-cdk CLI is required, as specified in the README. Please see the following link for installation: https://docs.aws.amazon.com/cdk/v2/guide/cli.html%b\n" "${RED}" "${NC}"; sh -c 'exit 1' )
	@printf "%bDependencies verified.%b\n" "${GREEN}" "${NC}"
