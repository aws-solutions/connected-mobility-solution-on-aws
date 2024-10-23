// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { constants } from "backstage-plugin-acdp-common";

import { AcdpMetricsApi } from ".";
import {
  mockedCatalogEntity,
  mockCatalogClient,
  mockedApplicationArn,
  mockedApplicationTag,
} from "../mocks";
import { MockedAcdpMetricsService } from "../service/mocks";

let mockedAcdpMetricsService: MockedAcdpMetricsService;
let acdpMetricsApi: AcdpMetricsApi;

beforeAll(async () => {
  mockedAcdpMetricsService = new MockedAcdpMetricsService();
  acdpMetricsApi = new AcdpMetricsApi(
    mockCatalogClient(mockedCatalogEntity),
    mockedAcdpMetricsService,
  );
});

describe("AcdpMetricsApi", () => {
  describe("getApplicationByEntity", () => {
    it("should return application", async () => {
      const application =
        await acdpMetricsApi.getApplicationByEntity(mockedCatalogEntity);

      expect(
        application?.applicationTag?.[
          constants.APP_REGISTRY_AWS_APPLICATION_TAG
        ],
      ).toEqual(
        mockedAcdpMetricsService.mockedApplication.applicationTag?.[
          constants.APP_REGISTRY_AWS_APPLICATION_TAG
        ],
      );
      expect(application?.arn).toEqual(
        mockedAcdpMetricsService.mockedApplication.arn,
      );
    });
  });

  describe("getApplicationByArn", () => {
    it("should return application", async () => {
      const application =
        await acdpMetricsApi.getApplicationByArn(mockedApplicationArn);

      expect(
        application?.applicationTag?.[
          constants.APP_REGISTRY_AWS_APPLICATION_TAG
        ],
      ).toEqual(
        mockedAcdpMetricsService.mockedApplication.applicationTag?.[
          constants.APP_REGISTRY_AWS_APPLICATION_TAG
        ],
      );
      expect(application?.arn).toEqual(
        mockedAcdpMetricsService.mockedApplication.arn,
      );
    });
  });

  describe("getNetUnblendedCurrentMonthCost", () => {
    it("should return the correct cost for a valid tag", async () => {
      const cost = await acdpMetricsApi.getNetUnblendedCurrentMonthCost(
        mockedCatalogEntity,
        mockedApplicationTag,
      );

      expect(cost).toEqual(
        mockedAcdpMetricsService.mockedNetUnblendedCurrentMonthCost,
      );
    });

    it("should return empty cost for an invalid tag", async () => {
      const cost = await acdpMetricsApi.getNetUnblendedCurrentMonthCost(
        mockedCatalogEntity,
        "invalid tag",
      );

      expect(cost).toEqual("");
    });
  });
});
