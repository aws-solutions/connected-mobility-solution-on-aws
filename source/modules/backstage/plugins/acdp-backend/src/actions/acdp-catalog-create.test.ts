// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { getVoidLogger } from "@backstage/backend-common";
import { mockClient } from "aws-sdk-client-mock";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { CatalogClient } from "@backstage/catalog-client";
import { fetchContents } from "@backstage/plugin-scaffolder-node";

import { createAcdpCatalogCreateAction } from ".";
import {
  mockDiscovery,
  mockUrlReader,
  mockConfig,
  mockIntegrations,
  mockedTemplateEntity,
  mockTemplateCatalogCreateInput,
  mockedCatalogEntity,
} from "../__mocks__/common-mocks";
import { stringifyEntityRef } from "@backstage/catalog-model";
import { Publisher, PublisherBase } from "@backstage/plugin-techdocs-node";
import { createMockDirectory } from "@backstage/backend-test-utils";
import { createMockActionContext } from "@backstage/plugin-scaffolder-node-test-utils";
import { mockServices } from "@backstage/backend-test-utils";

const mockedS3Client = mockClient(S3Client);
jest.mock("../service/acdp-build-service");

jest.mock("@backstage/plugin-scaffolder-node", () => ({
  ...jest.requireActual("@backstage/plugin-scaffolder-node"),
  fetchContents: jest.fn(),
  fetch: jest.fn(),
}));

jest.mock("@backstage/plugin-techdocs-node");
jest.mock("../utils/aws-s3-helper");

const mockPublisherBase = (): jest.Mocked<PublisherBase> => {
  const mock = {
    publish: jest.fn(),
    getReadiness: jest.fn(),
  };

  mock.publish.mockImplementation(() => Promise.resolve({}));
  mock.getReadiness.mockImplementation(() => Promise.resolve({}));

  return mock as Partial<
    jest.Mocked<PublisherBase>
  > as jest.Mocked<PublisherBase>;
};

Publisher.fromConfig = async () => mockPublisherBase();

beforeEach(() => {
  mockedS3Client.reset();
});

describe("createAcdpCatalogCreateAction", () => {
  const workspacePath = createMockDirectory().resolve("/tmp");

  it("", async () => {
    mockedS3Client.on(PutObjectCommand).resolves({
      ETag: "test",
    });

    const mockCatalogClient = (): jest.Mocked<CatalogClient> => {
      const mock = {
        getEntityByRef: jest.fn(),
        getLocationById: jest.fn(),
      };

      const determineReturn = (inputEntityRef: string) => {
        if (stringifyEntityRef(mockedCatalogEntity) === inputEntityRef) {
          return mockedCatalogEntity;
        }
        return undefined;
      };
      mock.getEntityByRef.mockImplementationOnce(async () => undefined);
      mock.getEntityByRef.mockImplementation(determineReturn);

      return mock as Partial<
        jest.Mocked<CatalogClient>
      > as jest.Mocked<CatalogClient>;
    };

    const catalogClient = mockCatalogClient();

    const mockContext = createMockActionContext({
      templateInfo: {
        baseUrl: "http://bucket.s3.com/my-template.yaml",
        entity: mockedTemplateEntity,
        entityRef: stringifyEntityRef(mockedTemplateEntity),
      },
      input: mockTemplateCatalogCreateInput,
      workspacePath: workspacePath,
    });

    await (
      await createAcdpCatalogCreateAction({
        config: mockConfig,
        reader: mockUrlReader,
        integrations: mockIntegrations,
        catalogClient: catalogClient,
        discovery: mockDiscovery,
        auth: mockServices.auth(),
        logger: getVoidLogger(),
      })
    ).handler(mockContext);

    expect(catalogClient.getEntityByRef.mock.calls.length === 2);
    expect(fetchContents).toHaveBeenCalledTimes(2);
    expect(mockedS3Client.calls()).toHaveLength(1);
    expect(mockContext.output).toHaveBeenCalledTimes(2);
  });
});
