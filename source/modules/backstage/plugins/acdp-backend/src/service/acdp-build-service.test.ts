// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  BatchGetBuildsCommand,
  BatchGetProjectsCommand,
  CodeBuildClient,
  ListBuildsForProjectCommand,
  StartBuildCommand,
} from "@aws-sdk/client-codebuild";
import { mockClient } from "aws-sdk-client-mock";
import {
  GetParameterCommand,
  PutParameterCommand,
  SSMClient,
} from "@aws-sdk/client-ssm";

import { AcdpBuildAction, constants } from "backstage-plugin-acdp-common";

import { getSsmParameterNameForEntitySourceConfig } from "./utils";
import { MockedAcdpBuildService } from "./mocks/acdp-build-service.mock";
import {
  mockSsmClientGetBuildParameters,
  mockedCatalogEntity,
  mockedConfigDataWithMultiAccount,
  resetUrlReaderMocks,
} from "../mocks";

const mockedCodeBuildClient = mockClient(CodeBuildClient);
const mockedSsmClient = mockClient(SSMClient);

let acdpBuildService: MockedAcdpBuildService;
beforeAll(async () => {
  acdpBuildService = new MockedAcdpBuildService();
});

beforeEach(() => {
  mockedCodeBuildClient.reset();
  mockedSsmClient.reset();
  resetUrlReaderMocks();
});

function setupCommonBuildMocks() {
  mockedCodeBuildClient.on(StartBuildCommand).resolves({
    build: {
      arn: "arn:aws:codebuild:us-west-2:111111111111:build/test:test",
      id: "test",
    },
  });

  mockedSsmClient.on(PutParameterCommand).resolves({
    Version: 1,
  });

  mockSsmClientGetBuildParameters(mockedSsmClient);

  mockedSsmClient
    .on(GetParameterCommand, {
      Name: getSsmParameterNameForEntitySourceConfig(
        mockedConfigDataWithMultiAccount.acdp.buildConfig
          .buildConfigStoreSsmPrefix,
        mockedCatalogEntity,
      ),
    })
    .resolves({
      Parameter: {
        Value: JSON.stringify({
          useEntityAssets: true,
        }),
      },
    });
}

describe("getProject", () => {
  it("should return project", async () => {
    mockedCodeBuildClient.on(BatchGetProjectsCommand).resolves({
      projects: [
        {
          arn: mockedConfigDataWithMultiAccount.acdp.deploymentDefaults
            .codeBuildProjectArn,
        },
      ],
    });

    const project = await acdpBuildService.getProject();

    expect(mockedCodeBuildClient.calls()).toHaveLength(1);
    expect(project?.arn).toEqual(
      mockedConfigDataWithMultiAccount.acdp.deploymentDefaults
        .codeBuildProjectArn,
    );
  });
});

describe("getBuilds", () => {
  it("should return builds filtered by BACKSTAGE_ENTITY_UID", async () => {
    const backstageEntityUid = mockedCatalogEntity.metadata.uid;
    mockedCodeBuildClient.on(ListBuildsForProjectCommand).resolves({
      ids: ["test-build-id-1", "test-build-id-2"],
    });
    mockedCodeBuildClient.on(BatchGetBuildsCommand).resolves({
      builds: [
        {
          buildNumber: 1,
          buildComplete: true,
          buildStatus: "SUCCEEDED",
          arn: "arn:aws:codebuild:us-west-2:111111111111:build/test:test",
          endTime: new Date("2023-01-01T23:34:38.397Z"),
          startTime: new Date("2023-01-01T23:31:26.086Z"),
          environment: {
            environmentVariables: [
              {
                name: constants.BACKSTAGE_ENTITY_UID_ENVIRONMENT_VARIABLE,
                value: backstageEntityUid,
              },
            ],
            computeType: "BUILD_GENERAL1_SMALL",
            image: "aws/codebuild/standard:5.0",
            type: "LINUX_CONTAINER",
          },
        },
        {
          buildNumber: 2,
          buildComplete: true,
          buildStatus: "SUCCEEDED",
          arn: "arn:aws:codebuild:us-west-2:111111111111:build/test:test",
          endTime: new Date("2023-01-01T23:34:38.397Z"),
          startTime: new Date("2023-01-01T23:31:26.086Z"),
          environment: {
            environmentVariables: [
              {
                name: "MODULE_STACK_NAME",
                value: "other-stack",
              },
            ],
            computeType: "BUILD_GENERAL1_SMALL",
            image: "aws/codebuild/standard:5.0",
            type: "LINUX_CONTAINER",
          },
        },
      ],
    });

    const builds = await acdpBuildService.getBuilds(mockedCatalogEntity);

    expect(mockedCodeBuildClient.calls()).toHaveLength(2);
    expect(builds).toHaveLength(1);
  });
  it("should return empty list for no builds", async () => {
    mockedCodeBuildClient.on(ListBuildsForProjectCommand).resolves({});

    const builds = await acdpBuildService.getBuilds(mockedCatalogEntity);

    expect(mockedCodeBuildClient.calls()).toHaveLength(1);
    expect(builds).toEqual([]);
  });
});

describe("startDeployBuild", () => {
  it("should startDeployBuild", async () => {
    setupCommonBuildMocks();

    await acdpBuildService.startBuild({
      entity: mockedCatalogEntity,
      action: AcdpBuildAction.DEPLOY,
    });

    expect(mockedSsmClient.calls()).toHaveLength(2);
    expect(mockedCodeBuildClient.calls()).toHaveLength(1);
  });
});

describe("startUpdateBuild", () => {
  it("should startUpdateBuild", async () => {
    setupCommonBuildMocks();

    await acdpBuildService.startBuild({
      entity: mockedCatalogEntity,
      action: AcdpBuildAction.UPDATE,
    });

    expect(mockedSsmClient.calls()).toHaveLength(2);
    expect(mockedCodeBuildClient.calls()).toHaveLength(1);
  });
});

describe("startTeardownBuild", () => {
  it("should startTeardownBuild", async () => {
    setupCommonBuildMocks();

    await acdpBuildService.startBuild({
      entity: mockedCatalogEntity,
      action: AcdpBuildAction.TEARDOWN,
    });

    expect(mockedSsmClient.calls()).toHaveLength(2);
    expect(mockedCodeBuildClient.calls()).toHaveLength(1);
  });
});
