// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { getVoidLogger } from "@backstage/backend-common";
import { mockClient } from "aws-sdk-client-mock";
import { CodeBuild, StartBuildCommand } from "@aws-sdk/client-codebuild";

import { createAcdpConfigureAction } from ".";
import {
  mockCatalogClient,
  mockUrlReader,
  mockConfig,
  mockedCatalogEntity,
  mockIntegrations,
  mockTokenManager,
} from "../__mocks__/common-mocks";
import { stringifyEntityRef } from "@backstage/catalog-model";
import { createMockDirectory } from "@backstage/backend-test-utils";
import { createMockActionContext } from "@backstage/plugin-scaffolder-node-test-utils";

jest.mock("../service/acdp-build-service");
const mockedCodeBuildClient = mockClient(CodeBuild);

beforeEach(() => {
  mockedCodeBuildClient.reset();
});

describe("createAcdpConfigureAction", () => {
  const workspacePath = createMockDirectory().resolve("/tmp");

  it("", async () => {
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
        config: mockConfig,
        reader: mockUrlReader,
        integrations: mockIntegrations,
        catalogClient: mockCatalogClient(mockedCatalogEntity),
        tokenManager: mockTokenManager,
        logger: getVoidLogger(),
      })
    ).handler(mockContext);
  });
});
