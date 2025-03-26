// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CostExplorerClient,
  GetCostAndUsageCommand,
} from "@aws-sdk/client-cost-explorer";
import { mockClient } from "aws-sdk-client-mock";
import { SSMClient } from "@aws-sdk/client-ssm";
import {
  GetApplicationCommand,
  ServiceCatalogAppRegistryClient,
} from "@aws-sdk/client-service-catalog-appregistry";

import { mockServices } from "@backstage/backend-test-utils";
import { constants } from "backstage-plugin-acdp-common";

import {
  mockedApplicationArn,
  mockedApplicationTag,
  mockedCurrentMonthCost,
  mockCredentialsProvider,
  mockSsmClientGetBuildParameters,
  mockedCatalogEntity,
  mockConfigWithoutMultiAccount,
} from "../mocks";
import {
  AcdpMetricsService,
  AcdpMetricsServiceOptions,
} from "./acdp-metrics-service";

const mockedAppRegistryClient = mockClient(ServiceCatalogAppRegistryClient);
const mockedCostExplorerClient = mockClient(CostExplorerClient);
const mockedSsmClient = mockClient(SSMClient);

let acdpMetricsService: AcdpMetricsService;
beforeAll(async () => {
  const acdpMetricsServiceMockedOptions: AcdpMetricsServiceOptions = {
    config: mockConfigWithoutMultiAccount,
    awsCredentialsProvider: mockCredentialsProvider,
    logger: mockServices.logger.mock(),
  };
  acdpMetricsService = new AcdpMetricsService(acdpMetricsServiceMockedOptions);
});

beforeEach(() => {
  mockedSsmClient.reset();
  mockedAppRegistryClient.reset();
  mockedCostExplorerClient.reset();
});

describe("AcdpMetricsService", () => {
  describe("getApplicationByEntity", () => {
    it("should return application", async () => {
      mockSsmClientGetBuildParameters(mockedSsmClient);

      mockedAppRegistryClient.on(GetApplicationCommand).resolves({
        arn: mockedApplicationArn,
        applicationTag: {
          [constants.APP_REGISTRY_AWS_APPLICATION_TAG]: mockedApplicationTag,
        },
      });

      const application =
        await acdpMetricsService.getApplicationByEntity(mockedCatalogEntity);

      expect(mockedSsmClient.calls()).toHaveLength(1);
      expect(mockedAppRegistryClient.calls()).toHaveLength(1);
      expect(
        application?.applicationTag?.[
          constants.APP_REGISTRY_AWS_APPLICATION_TAG
        ],
      ).toEqual(mockedApplicationTag);
      expect(application?.arn).toEqual(mockedApplicationArn);
    });
  });

  describe("getApplicationByArn", () => {
    it("should return application", async () => {
      mockSsmClientGetBuildParameters(mockedSsmClient);

      mockedAppRegistryClient.on(GetApplicationCommand).resolves({
        arn: mockedApplicationArn,
        applicationTag: {
          [constants.APP_REGISTRY_AWS_APPLICATION_TAG]: mockedApplicationTag,
        },
      });

      const application =
        await acdpMetricsService.getApplicationByEntity(mockedCatalogEntity);

      expect(mockedSsmClient.calls()).toHaveLength(1);
      expect(mockedAppRegistryClient.calls()).toHaveLength(1);
      expect(
        application?.applicationTag?.[
          constants.APP_REGISTRY_AWS_APPLICATION_TAG
        ],
      ).toEqual(mockedApplicationTag);
      expect(application?.arn).toEqual(mockedApplicationArn);
    });
  });

  describe("getNetUnblendedCurrentMonthCost", () => {
    it("should return correct cost with valid application tag", async () => {
      const mockedOutput = {
        ResultsByTime: [
          {
            Total: {
              NetUnblendedCost: {
                Amount: mockedCurrentMonthCost,
              },
            },
          },
        ],
      };
      mockedCostExplorerClient
        .on(GetCostAndUsageCommand)
        .resolves(mockedOutput);

      const cost = await acdpMetricsService.getNetUnblendedCurrentMonthCost(
        mockedCatalogEntity,
        mockedApplicationTag,
      );

      expect(mockedCostExplorerClient.calls()).toHaveLength(1);
      expect(cost).toEqual(mockedCurrentMonthCost);
    });
  });
});
