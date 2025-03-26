// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { DiscoveryService } from "@backstage/backend-plugin-api";
import { stringifyEntityRef } from "@backstage/catalog-model";
import { mockedCatalogEntity } from "../../mocks";

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

export const mockDiscovery: jest.Mocked<DiscoveryService> = {
  getBaseUrl: jest.fn().mockResolvedValue("http://localhost:8080/api/acdp"),
  getExternalBaseUrl: jest.fn(),
};
