// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { stringifyEntityRef } from "@backstage/catalog-model";

import { AcdpMetricsApi } from ".";
import {
  mockMetricsEntity,
  mockGlobalFetch,
  mockAcdpBaseApiInput,
  baseUrl,
} from "../mocks";

const acdpMetricsApiClient = new AcdpMetricsApi(mockAcdpBaseApiInput);

let mockedFetch: jest.SpyInstance;
beforeEach(() => {
  mockedFetch = mockGlobalFetch();
});

afterEach(() => {
  jest.clearAllMocks();
});

describe("AcdpMetricsApi", () => {
  it("should get Application by entity", async () => {
    await acdpMetricsApiClient.getApplicationByEntity({
      entityRef: stringifyEntityRef(mockMetricsEntity),
    });

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp-backend/application/by-entity?entityRef=component%3Aacdp-metrics%2Fcms-sample`,
    );
  });

  it("should get Application by arn", async () => {
    const mockedApplicationArn =
      "arn:aws:servicecatalog:us-east-2:111111111111:/applications/test-application-id";
    await acdpMetricsApiClient.getApplicationByArn(mockedApplicationArn);

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp-backend/application/by-arn?arn=arn%3Aaws%3Aservicecatalog%3Aus-east-2%3A111111111111%3A%2Fapplications%2Ftest-application-id`,
    );
  });

  it("should get cost/current-month-net-unblended", async () => {
    await acdpMetricsApiClient.getNetUnblendedCurrentMonthCost({
      entityRef: stringifyEntityRef(mockMetricsEntity),
      awsApplicationTag: "mocked-aws-application-tag",
    });

    const fetchCall = mockedFetch.mock.calls[0][0].valueOf() as Request;
    expect(fetchCall.method).toEqual("GET");
    expect(fetchCall.url).toEqual(
      `${baseUrl}/api/acdp-backend/cost/current-month-net-unblended?entityRef=component%3Aacdp-metrics%2Fcms-sample&awsApplicationTag=mocked-aws-application-tag`,
    );
  });
});
