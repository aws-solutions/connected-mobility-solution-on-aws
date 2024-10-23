// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  Build,
  Project,
  StartBuildCommandOutput,
} from "@aws-sdk/client-codebuild";

import { Entity } from "@backstage/catalog-model";

import { constants } from "backstage-plugin-acdp-common";

import { StartBuildInput } from "../api";

export class MockAcdpBuildApi {
  async getProject(): Promise<Project> {
    return {
      name: "test-project",
      arn: "arn:aws:codebuild:us-west-2:111111111111:project/test-project",
      environment: {
        type: "LINUX_CONTAINER",
        image: "aws/codebuild/amazonlinux2-x86_64-standard:3.0",
        computeType: "BUILD_GENERAL1_SMALL",
        privilegedMode: false,
        imagePullCredentialsType: "CODEBUILD",
      },
      created: new Date("2022-05-20T13:58:29.342000-06:00"),
      lastModified: new Date("2022-05-20T13:58:29.342000-06:00"),
    };
  }

  async listBuilds({ stackName }: { stackName: string }): Promise<Build[]> {
    return [
      {
        arn: "arn:aws:codebuild:us-west-2:111111111111:project/test-project",
        buildComplete: true,
        buildNumber: 1,
        buildStatus: "SUCCEEDED",
        currentPhase: "COMPLETED",
        endTime: new Date("2022-04-14T23:34:38.397Z"),
        startTime: new Date("2022-04-14T23:31:26.086Z"),
        environment: {
          computeType: "BUILD_GENERAL1_SMALL",
          environmentVariables: [],
          image: "aws/codebuild/standard:5.0",
          imagePullCredentialsType: "CODEBUILD",
          privilegedMode: false,
          type: "LINUX_CONTAINER",
        },
        exportedEnvironmentVariables: [
          {
            name: constants.MODULE_STACK_NAME_ENVIRONMENT_VARIABLE,
            value: stackName,
          },
        ],
      },
      {
        arn: "arn:aws:codebuild:us-west-2:111111111111:project/test-project",
        buildComplete: true,
        buildNumber: 2,
        buildStatus: "SUCCEEDED",
        currentPhase: "COMPLETED",
        endTime: new Date("2022-04-14T23:34:38.397Z"),
        startTime: new Date("2022-04-14T23:31:26.086Z"),
        environment: {
          computeType: "BUILD_GENERAL1_SMALL",
          environmentVariables: [],
          image: "aws/codebuild/standard:5.0",
          imagePullCredentialsType: "CODEBUILD",
          privilegedMode: false,
          type: "LINUX_CONTAINER",
        },
        exportedEnvironmentVariables: [
          {
            name: constants.MODULE_STACK_NAME_ENVIRONMENT_VARIABLE,
            value: stackName,
          },
        ],
      },
    ];
  }

  async startBuild(_: StartBuildInput): Promise<StartBuildCommandOutput> {
    // Wait for 1 second so that progress bar element can be properly tested
    await new Promise((r) => setTimeout(r, 1001));
    return {
      $metadata: {},
    };
  }
}

export const mockCodeBuildEntity: Entity = {
  apiVersion: "backstage.io/v1alpha1",
  kind: "Component",
  metadata: {
    uid: "uniqueId",
    annotations: {
      "aws.amazon.com/acdp-deploy-on-create": "true",
      "aws.amazon.com/acdp-deployment-target": "default",
      "aws.amazon.com/techdocs-builder": "external",
      "backstage.io/techdocs-ref": "dir:.",
      "aws.amazon.com/template-entity-ref": "template:default/cms-sample",
      "aws.amazon.com/acdp-assets-ref": "dir:assets",
      "backstage.io/source-location":
        "url:https://test-bucket.s3.us-west-2.amazonaws.com/local/backstage/catalog/acdp/component/cms-sample/assets",
    },
    description:
      "A CDK Python app for showing a basic skeleton for a CMS module",
    name: "cms-sample",
    namespace: "acdp-build",
  },
  spec: {
    lifecycle: "experimental",
    owner: "group:default/mock",
    type: "service",
  },
};
