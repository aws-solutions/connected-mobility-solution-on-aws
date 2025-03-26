// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { mockClient } from "aws-sdk-client-mock";
import { CodeBuild, StartBuildCommand } from "@aws-sdk/client-codebuild";

import { stringifyEntityRef } from "@backstage/catalog-model";
import {
  createMockDirectory,
  mockServices,
} from "@backstage/backend-test-utils";
import { createMockActionContext } from "@backstage/plugin-scaffolder-node-test-utils";

import { createAcdpConfigureAction } from ".";
import {
  mockCatalogClient,
  mockUrlReader,
  mockConfigWithoutMultiAccount,
  mockedCatalogEntity,
  mockIntegrations,
} from "../mocks";

jest.mock("../service/acdp-build-service");
const mockedCodeBuildClient = mockClient(CodeBuild);

beforeEach(() => {
  mockedCodeBuildClient.reset();
});

describe("createAcdpConfigureAction", () => {
  const workspacePath = createMockDirectory().resolve("/tmp");

  it("creates ACDP configure action", async () => {
    const mockContext = createMockActionContext({
      templateInfo: {
        entityRef: stringifyEntityRef(mockedCatalogEntity),
      },
      input: {
        entityRef: stringifyEntityRef(mockedCatalogEntity),
        buildParameters: [{ name: "test", value: "test" }],
      },
      workspacePath: workspacePath,
    });

    mockedCodeBuildClient.on(StartBuildCommand).resolves({
      build: {
        arn: "arn:aws:codebuild:us-west-2:111111111111:build/test:test",
        id: "test",
      },
    });

    await (
      await createAcdpConfigureAction({
        config: mockConfigWithoutMultiAccount,
        reader: mockUrlReader,
        integrations: mockIntegrations,
        catalogClient: mockCatalogClient(mockedCatalogEntity),
        auth: mockServices.auth(),
        logger: mockServices.logger.mock(),
      })
    ).handler(mockContext);

    expect(mockedCodeBuildClient.commandCalls).toHaveLength(3);
  });
});
