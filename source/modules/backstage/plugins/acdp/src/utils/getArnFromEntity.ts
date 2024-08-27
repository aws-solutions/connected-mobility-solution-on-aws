// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { validate, parse } from "@aws-sdk/util-arn-parser";

export function parseCodeBuildArn(arn: string): {
  arn: string;
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

  if (resourceParts.length !== 2)
    throw new Error(`CodeBuild ARN not valid: ${arn}`);

  return { projectName: resourceParts[1], arn: arn, ...parsedArn };
}
