// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { EnvironmentVariable, SourceType } from "@aws-sdk/client-codebuild";
import { validate, parse } from "@aws-sdk/util-arn-parser";

import { Entity, stringifyEntityRef } from "@backstage/catalog-model";
import { InputError } from "@backstage/errors";

import { constants, AcdpDeploymentTarget } from "backstage-plugin-acdp-common";

export function getCodeBuildSourceTypeForUrl(url: string): SourceType {
  const githubPattern = /^https?:\/\/(www\.)?github\.com\/.+$/;
  const s3Pattern =
    /^https?:\/\/([a-z0-9-]+\.)?s3[\.-]([a-z0-9-]+\.)?amazonaws\.com\/.+/;

  if (githubPattern.test(url)) {
    return SourceType.GITHUB;
  } else if (s3Pattern.test(url)) {
    return SourceType.S3;
  }

  return SourceType.NO_SOURCE;
}

export function getDeploymentTargetForEntity(
  entity: Entity,
  codebuildArn: string,
): AcdpDeploymentTarget {
  const annotations = entity.metadata.annotations!;

  const deploymentTargetAccount =
    annotations[constants.ACDP_DEPLOYMENT_TARGET_ACCOUNT_ANNOTATION];

  const deploymentTargetRegion =
    annotations[constants.ACDP_DEPLOYMENT_TARGET_REGION_ANNOTATION];

  if (!deploymentTargetAccount) {
    throw new InputError(
      `No deployment account is set under annotation '${constants.ACDP_DEPLOYMENT_TARGET_ACCOUNT_ANNOTATION}'`,
    );
  }

  if (!deploymentTargetRegion) {
    throw new InputError(
      `No deployment region is set under annotation '${constants.ACDP_DEPLOYMENT_TARGET_REGION_ANNOTATION}'`,
    );
  }

  return {
    awsAccountId: deploymentTargetAccount,
    awsRegion: deploymentTargetRegion,
    codeBuildArn: codebuildArn,
  };
}

export function formatS3UrlToPath(url: string): string {
  const urlObject = new URL(url);

  let bucket: string;
  const s3_path: string = urlObject.pathname.substring(1);

  if (urlObject.hostname.endsWith("s3.amazonaws.com")) {
    bucket = urlObject.hostname.split(".s3.amazonaws.com")[0];
  } else {
    bucket = urlObject.hostname.split(".s3.")[0];
  }

  return `${bucket}/${s3_path}`;
}

export function getDeploymentTargetFromArn(
  arn: string,
  codebuildArn: string,
): AcdpDeploymentTarget {
  if (!validate(arn))
    throw new Error(`Value for arn was not a valid ARN: '${arn}'`);

  const parsedArn = parse(arn);
  return {
    awsAccountId: parsedArn.accountId,
    awsRegion: parsedArn.region,
    codeBuildArn: codebuildArn,
  };
}

export function parseCodeBuildArn(arn: string): {
  accountId: string;
  region: string;
  service: string;
  resource: string;
  projectName: string;
} {
  if (!validate(arn))
    throw new Error(`Value for codebuild arn was not a valid ARN: '${arn}'`);

  const parsedArn = parse(arn);
  const resourceParts = parsedArn.resource.split("/");
  const projectName = resourceParts[1].split(":")[0];

  return { projectName, ...parsedArn };
}

export function removeUrlPrefix(input: string): string {
  return input.replace(/^url:/, "");
}

export function updateEnvironmentVariablesForDeploymentTarget(
  deploymentTarget: AcdpDeploymentTarget,
  entity: Entity,
  environmentVariables: EnvironmentVariable[] = [],
) {
  const overrideValues = [
    {
      name: "AWS_ACCOUNT_ID",
      value: deploymentTarget.awsAccountId,
    },
    {
      name: "AWS_REGION",
      value: deploymentTarget.awsRegion,
    },
    {
      name: constants.BACKSTAGE_ENTITY_UID_ENVIRONMENT_VARIABLE,
      value: entity.metadata.uid,
    },
    {
      name: "BACKSTAGE_ENTITY_REF",
      value: stringifyEntityRef(entity),
    },
  ];

  for (const variableOverride of overrideValues) {
    const variableIndex = environmentVariables.findIndex(
      (x) => x.name === variableOverride.name,
    );
    if (variableIndex >= 0) {
      environmentVariables[variableIndex].value = variableOverride.value;
    } else {
      environmentVariables.push(variableOverride);
    }
  }

  return environmentVariables;
}
