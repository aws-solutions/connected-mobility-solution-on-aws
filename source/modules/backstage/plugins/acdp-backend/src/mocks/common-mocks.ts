// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AwsStub } from "aws-sdk-client-mock";
import { GetParameterCommand } from "@aws-sdk/client-ssm";

import { UrlReader } from "@backstage/backend-common";
import {
  CatalogClient,
  CatalogRequestOptions,
} from "@backstage/catalog-client";
import {
  CompoundEntityRef,
  Entity,
  stringifyEntityRef,
} from "@backstage/catalog-model";
import { ConfigReader } from "@backstage/config";
import { ScmIntegrations } from "@backstage/integration";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";

import { mockedConfigData } from "./build-mocks";
import { getSsmParameterNameForEntityBuildParameters } from "../service/utils";

export const mockedCatalogEntity = {
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
        "url:https://test-bucket.s3.us-west-2.amazonaws.com/local/backstage/catalog/acdp/component/cms-sample/assets/",
    },
    description:
      "A CDK Python app for showing a basic skeleton for a CMS module",
    name: "cms-sample",
    namespace: "acdp",
  },
  spec: {
    lifecycle: "experimental",
    owner: "group:default/asdf",
    type: "service",
  },
};

export const mockConfig = new ConfigReader(mockedConfigData);

export const mockCredentialsProvider = {
  sdkCredentialProvider: jest.fn().mockResolvedValue({
    accessKeyId: "asdfasdf",
    secretAccessKey: "asdfasdf",
    sessionToken: "asdfasdf",
  }),
} satisfies AwsCredentialProvider;

export const mockUrlReader: jest.Mocked<UrlReader> = {
  readUrl: jest.fn(),
  readTree: jest.fn(),
  search: jest.fn(),
};

export function resetUrlReaderMocks() {
  mockUrlReader.readUrl.mockReset();
  mockUrlReader.readTree.mockReset();
  mockUrlReader.search.mockReset();

  mockUrlReader.readUrl.mockResolvedValue({
    buffer: jest
      .fn()
      .mockResolvedValue(Buffer.from(JSON.stringify({ a: ["b", 7] }), "utf-8")),
  });
}

export const mockCatalogClient = (
  entity?: Entity,
): jest.Mocked<CatalogClient> => {
  const mock = {
    getEntityByRef: jest.fn(),
    getLocationById: jest.fn(),
  };
  if (entity) {
    const determineReturn = async (
      inputEntityRef: string | CompoundEntityRef,
      _?: CatalogRequestOptions,
    ) => {
      if (
        (typeof inputEntityRef === "string" &&
          stringifyEntityRef(entity) === inputEntityRef) ||
        stringifyEntityRef(entity) ===
          stringifyEntityRef(inputEntityRef as CompoundEntityRef)
      ) {
        return entity;
      }

      return undefined;
    };
    mock.getEntityByRef.mockImplementation(
      (inputEntityRef, catalogRequestOptions) =>
        determineReturn(inputEntityRef, catalogRequestOptions),
    );
  }
  return mock as Partial<
    jest.Mocked<CatalogClient>
  > as jest.Mocked<CatalogClient>;
};

export const mockIntegrations = ScmIntegrations.fromConfig(mockConfig);

export const mockSsmClientGetBuildParameters = (
  mockedSsmClient: AwsStub<any, any, any>,
) => {
  mockedSsmClient
    .on(GetParameterCommand, {
      Name: getSsmParameterNameForEntityBuildParameters(
        mockedConfigData.acdp.buildConfig.buildConfigStoreSsmPrefix,
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
              "https://acdp-assets.s3.us-west-2.amazonaws.com/connected-mobility-solution-on-aws/vX.X.X/cms-sample/cms-sample.template",
          },
          { name: "APP_UNIQUE_ID", value: "cms" },
        ]),
      },
    });
};
