// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  PluginEndpointDiscovery,
  TokenManager,
  UrlReader,
} from "@backstage/backend-common";
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
import { AuthenticationError } from "@backstage/errors";
import { ScmIntegrations } from "@backstage/integration";
import { AwsCredentialProvider } from "@backstage/integration-aws-node";

export const mockedConfigData = {
  acdp: {
    s3Catalog: {
      bucketName: "bucket",
      prefix: "test/backstage/catalog",
      region: "us-west-2",
    },
    buildConfig: {
      buildConfigStoreSsmPrefix: "/local/backstage/acdp-build",
    },
    deploymentDefaults: {
      region: "us-west-2",
      accountId: "111111111111",
      codeBuildProjectArn:
        "arn:aws:codebuild:us-west-2:111111111111:project/test",
    },
    metrics: {
      userAgentString: "local-user-agent",
    },
  },
  techdocs: {
    generator: {
      runIn: "local",
    },
    builder: "local",
    publisher: {
      type: "awsS3",
      awsS3: {
        bucketName: "bucket",
        region: "us-west-2",
        bucketRootPath: "test/backstage/techdocs",
      },
    },
  },
};

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

export const mockTemplateCatalogCreateInput = {
  assetsSourcePath: "dir:../acdp/cms-sample/",
  componentId: "cms-sample",
  docsSiteSourcePath: "dir:../docs/components/cms-sample/site/",
  entity: {
    apiVersion: "backstage.io/v1alpha1",
    kind: "Component",
    metadata: {
      annotations: {
        "aws.amazon.com/acdp-deploy-on-create": "true",
      },
      description: "sample description",
      name: "cms-sample",
      namespace: "acdp",
    },
    spec: {
      lifecycle: "experimental",
      owner: "test",
      type: "service",
    },
  },
};

export const mockedTemplateEntity = {
  apiVersion: "scaffolder.backstage.io/v1beta3",
  kind: "Template",
  metadata: {
    description:
      "A CDK Python app for showing a basic skeleton for a CMS module",
    name: "cms-sample",
    tags: ["cms", "guide", "sample"],
    title: "CMS Sample Module",
  },
  spec: {
    output: {
      links: [
        {
          entityRef: stringifyEntityRef(mockedCatalogEntity),
          icon: "catalog",
          title: "Open in catalog",
        },
      ],
    },
    owner: "aws solutions",
    parameters: [
      {
        properties: {
          componentId: {
            default: "cms-sample",
            description: "Unique name of the component",
            pattern: "[a-zA-Z][-a-zA-Z0-9]*[a-zA-Z]",
            title: "Name",
            type: "string",
            "ui:field": "EntityNamePicker",
          },
          description: {
            default:
              "A CDK Python app for showing a basic skeleton for a CMS module",
            description: "Help others understand what this component is for.",
            title: "Description",
            type: "string",
          },
          owner: {
            description: "Owner of the component",
            title: "Owner",
            type: "string",
            "ui:field": "OwnerPicker",
            "ui:options": {
              catalogFilter: {
                kind: ["Group", "User"],
              },
            },
          },
        },
        required: ["componentId", "owner"],
        title: "Provide the required information",
      },
      {
        properties: {
          appUniqueId: {
            default: "cms",
            description:
              "Application unique identifier used to uniquely name resources within the stack",
            title: "App Unique ID",
            type: "string",
            "ui:disabled": true,
          },
        },
        required: ["appUniqueId"],
        title: "Provide the Module Configuration",
      },
    ],
    steps: [
      {
        action: "aws:acdp:catalog:create",
        id: "acdpCatalogCreate",
        input: mockTemplateCatalogCreateInput,
        name: "ACDP S3 Catalog Write",
      },
      {
        action: "catalog:register",
        id: "catalogRegister",
        input: {
          catalogInfoUrl: "https://test",
        },
        name: "Backstage Catalog Register",
      },
      {
        action: "aws:acdp:configure",
        id: "acdpConfigureDeploy",
        input: {
          buildParameters: [
            {
              name: "CFN_TEMPLATE_URL",
              value:
                "https://acdp-assets.s3.us-west-2.amazonaws.com/connected-mobility-solution-on-aws/v0.0.0/cms-sample/cms-sample.template",
            },
            {
              name: "APP_UNIQUE_ID",
              value: "cms",
            },
          ],
          entityRef: "dummy",
        },
        name: "ACDP Deploy",
      },
    ],
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

export const mockDiscovery: jest.Mocked<PluginEndpointDiscovery> = {
  getBaseUrl: jest.fn().mockResolvedValue("http://localhost:8080/api/acdp"),
  getExternalBaseUrl: jest.fn(),
};

const mockTestToken = "test-token";
export const mockTokenManager: jest.Mocked<TokenManager> = {
  authenticate: jest.fn().mockImplementation((token) => {
    if (token !== mockTestToken)
      throw new AuthenticationError("Token mismatch");
  }),
  getToken: jest.fn().mockResolvedValue(mockTestToken),
};

export function resetMocks() {
  mockUrlReader.readUrl.mockReset();
  mockUrlReader.readTree.mockReset();
  mockUrlReader.search.mockReset();

  setupMocks();
}

export function setupMocks() {
  mockUrlReader.readUrl.mockResolvedValue({
    buffer: jest
      .fn()
      .mockResolvedValue(Buffer.from(JSON.stringify({ a: ["b", 7] }), "utf-8")),
  });
}
