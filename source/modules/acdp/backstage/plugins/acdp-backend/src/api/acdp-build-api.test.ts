// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { mockClient } from "aws-sdk-client-mock";
import { AcdpBuildApi } from ".";
import {
  BatchGetProjectsCommand,
  CodeBuildClient,
  ListBuildsForProjectCommand,
  BatchGetBuildsCommand,
  StartBuildCommand,
} from "@aws-sdk/client-codebuild";
import {
  mockUrlReader,
  mockedConfigData,
  mockedCatalogEntity,
  resetMocks,
  mockCatalogClient,
} from "../__mocks__/common-mocks";
import { AcdpBuildAction, constants } from "backstage-plugin-acdp-common";
import { GetParameterCommand, SSMClient } from "@aws-sdk/client-ssm";
import { MockedAcdpBuildService } from "../service/__mocks__/acdp-build-service.mock";

const mockedCodeBuildClient = mockClient(CodeBuildClient);
const mockedSsmClient = mockClient(SSMClient);
let mockedAcdpBuildService: MockedAcdpBuildService;
let acdpBuildApi: AcdpBuildApi;
beforeAll(async () => {
  mockedAcdpBuildService = new MockedAcdpBuildService();
  acdpBuildApi = new AcdpBuildApi(
    mockCatalogClient(mockedCatalogEntity),
    mockedAcdpBuildService,
  );
});

beforeEach(() => {
  mockedCodeBuildClient.reset();
  mockedSsmClient.reset();
  resetMocks();
});

function setupCommonBuildMocks() {
  mockedCodeBuildClient.on(StartBuildCommand).resolves({});

  mockedSsmClient
    .on(GetParameterCommand, {
      Name: mockedAcdpBuildService.getSsmParameterNameForEntityBuildParameters(
        mockedCatalogEntity,
      ),
    })
    .resolves({
      Parameter: {
        Value: JSON.stringify([
          { name: "MODULE_STACK_NAME", value: "acdp-cms-sample" },
          {
            name: "CFN_TEMPLATE_URL",
            value:
              "https://acdp-assets.s3.us-west-2.amazonaws.com/connected-mobility-solution-on-aws/v1.1.2/cms-sample/cms-sample.template",
          },
          { name: "APP_UNIQUE_ID", value: "cms" },
        ]),
      },
    });

  mockedSsmClient
    .on(GetParameterCommand, {
      Name: mockedAcdpBuildService.getSsmParameterNameForEntitySourceConfig(
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

describe("AcdpBuildApi", () => {
  describe("getProject", () => {
    it("should return project", async () => {
      mockedCodeBuildClient.on(BatchGetProjectsCommand).resolves({
        projects: [
          {
            arn: mockedConfigData.acdp.deploymentDefaults.codeBuildProjectArn,
          },
        ],
      });

      const project = await acdpBuildApi.getProject(mockedCatalogEntity);

      expect(mockedCodeBuildClient.calls()).toHaveLength(1);
      expect(project?.arn).toEqual(
        mockedConfigData.acdp.deploymentDefaults.codeBuildProjectArn,
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

      const builds = await acdpBuildApi.getBuilds(mockedCatalogEntity);

      expect(mockedCodeBuildClient.calls()).toHaveLength(2);
      expect(builds).toHaveLength(1);
    });

    it("should return empty list for no builds", async () => {
      mockedCodeBuildClient.on(ListBuildsForProjectCommand).resolves({});

      const builds = await acdpBuildApi.getBuilds(mockedCatalogEntity);

      expect(mockedCodeBuildClient.calls()).toHaveLength(1);
      expect(builds).toEqual([]);
    });
  });

  describe("startDeployBuild", () => {
    it("should startDeployBuild", async () => {
      setupCommonBuildMocks();

      await acdpBuildApi.startBuild(
        mockedCatalogEntity,
        AcdpBuildAction.DEPLOY,
      );

      expect(mockUrlReader.readUrl.mock.calls).toHaveLength(1);
      expect(mockedCodeBuildClient.calls()).toHaveLength(1);
    });
  });

  describe("startUpdateBuild", () => {
    it("should startUpdateBuild", async () => {
      setupCommonBuildMocks();

      await acdpBuildApi.startBuild(
        mockedCatalogEntity,
        AcdpBuildAction.UPDATE,
      );

      expect(mockUrlReader.readUrl.mock.calls).toHaveLength(1);
      expect(mockedCodeBuildClient.calls()).toHaveLength(1);
    });
  });

  describe("startTeardownBuild", () => {
    it("should startTeardownBuild", async () => {
      setupCommonBuildMocks();

      await acdpBuildApi.startBuild(
        mockedCatalogEntity,
        AcdpBuildAction.DEPLOY,
      );

      expect(mockUrlReader.readUrl.mock.calls).toHaveLength(1);
      expect(mockedCodeBuildClient.calls()).toHaveLength(1);
    });
  });
});
