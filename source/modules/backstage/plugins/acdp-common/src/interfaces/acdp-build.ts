// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { SourceType } from "@aws-sdk/client-codebuild";
import { Entity } from "@backstage/catalog-model";

export interface AcdpDeploymentTarget {
  awsAccountId: string;
  awsRegion: string;
  codeBuildArn: string;
  codeBuildIamRoleOverrideArn?: string;
}

export interface AcdpBuildProject {
  name?: string;
  arn?: string;
}

export interface AcdpBuildProjectBuild {
  id?: string;
  arn?: string;
  buildNumber?: number;
  startTime?: Date;
  endTime?: Date;
  currentPhase?: string;
  buildStatus?: string;
  projectName?: string;
}

export enum AcdpBuildAction {
  DEPLOY = "deploy",
  UPDATE = "update",
  TEARDOWN = "teardown",
}

export interface AcdpBuildInput {
  entity: Entity;
}

export interface BuildSourceConfig {
  useEntityAssets: boolean;
  sourceType?: SourceType;
  sourceLocation?: string;
  sourceVersion?: string;
}
