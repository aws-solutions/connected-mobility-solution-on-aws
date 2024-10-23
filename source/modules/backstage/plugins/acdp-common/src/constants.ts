// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Annotation Keys
export const ACDP_DEPLOY_ON_CREATE_ANNOTATION =
  "aws.amazon.com/acdp-deploy-on-create";
export const ACDP_DEPLOYMENT_TARGET_ANNOTATION =
  "aws.amazon.com/acdp-deployment-target";
export const ACDP_DEPLOY_BUILDSPEC_ANNOTATION =
  "aws.amazon.com/acdp-deploy-buildspec";
export const ACDP_UPDATE_BUILDSPEC_ANNOTATION =
  "aws.amazon.com/acdp-update-buildspec";
export const ACDP_TEARDOWN_BUILDSPEC_ANNOTATION =
  "aws.amazon.com/acdp-teardown-buildspec";
export const APP_REGISTRY_APPLICATION_ARN_ANNOTATION =
  "aws.amazon.com/app-registry-application-arn";

export const BACKSTAGE_TECHDOCS_ANNOTATION = "backstage.io/techdocs-ref";

export const ACDP_ASSETS_REF = "aws.amazon.com/acdp-assets-ref";
export const ACDP_ASSETS_STORED = "aws.amazon.com/acdp-assets-stored";

// Anotation Values
export const ACDP_DEFAULT_DEPLOYMENT_TARGET = "default";
export const ACDP_DEFAULT_DEPLOY_BUILDSPEC_LOCATION =
  "dir:./.acdp/deploy.buildspec.yaml";
export const ACDP_DEFAULT_UPDATE_BUILDSPEC_LOCATION =
  "dir:./.acdp/update.buildspec.yaml";
export const ACDP_DEFAULT_TEARDOWN_BUILDSPEC_LOCATION =
  "dir:./.acdp/teardown.buildspec.yaml";

// Environment Variable Keys
export const BACKSTAGE_ENTITY_UID_ENVIRONMENT_VARIABLE = "BACKSTAGE_ENTITY_UID";
export const MODULE_STACK_NAME_ENVIRONMENT_VARIABLE = "MODULE_STACK_NAME";

// SSM Names
export const BUILD_PARAMETER_SSM_POSTFIX = "build-parameters";
export const BUILD_SOURCE_CONFIG_SSM_POSTFIX = "source-config";

// Tag Keys
export const APP_REGISTRY_AWS_APPLICATION_TAG = "awsApplication";
