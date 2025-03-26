// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express, { NextFunction, Request, Response } from "express";
import request from "supertest";

import { mockServices } from "@backstage/backend-test-utils";
import { stringifyEntityRef } from "@backstage/catalog-model";
import { AuthorizeResult } from "@backstage/plugin-permission-common";

import { createAcdpMetricsRouter } from ".";
import {
  mockedApplicationArn,
  mockedApplicationTag,
  mockCatalogClient,
  mockedCatalogEntity,
  resetUrlReaderMocks,
  mockedCurrentMonthCost,
} from "../mocks";
import { MockedAcdpMetricsService } from "../service/mocks";
import { MockedAcdpMetricsApi } from "../api/mocks";

let mockedAcdpMetricsApi: MockedAcdpMetricsApi;
let app: express.Express;
const permissions = mockServices.permissions.mock();

const mockIsAuthenticated = (req: Request, _: Response, next: NextFunction) => {
  req.user = { token: "test-token" };
  return next();
};

beforeEach(async () => {
  const mockedAcdpMetricsService = new MockedAcdpMetricsService();
  mockedAcdpMetricsApi = new MockedAcdpMetricsApi(
    mockCatalogClient(mockedCatalogEntity),
    mockedAcdpMetricsService,
  );

  jest
    .spyOn(permissions, "authorize")
    .mockResolvedValue([{ result: AuthorizeResult.ALLOW }]);
  const router = await createAcdpMetricsRouter({
    acdpMetricsApi: mockedAcdpMetricsApi,
    auth: mockServices.auth(),
    httpAuth: mockServices.httpAuth(),
    permissions: permissions,
  });

  app = express().use(mockIsAuthenticated, router);
});

beforeEach(() => {
  resetUrlReaderMocks();
});

describe("GET /application/by-entity", () => {
  it("should return 200 status for valid request", async () => {
    const response = await request(app).get(
      `/application/by-entity?entityRef=${stringifyEntityRef(
        mockedCatalogEntity,
      )}`,
    );

    expect(response.status).toEqual(200);
    expect(response.body).toEqual(mockedAcdpMetricsApi.mockedApplication);
  });

  it("should return 400 status for invalid request", async () => {
    const response = await request(app).get(
      `/application/by-entity?entityRef=invalid-entity-ref`,
    );

    expect(response.status).toEqual(400);
  });

  it("should return NotAllowedError for unauthorized request", async () => {
    jest
      .spyOn(permissions, "authorize")
      .mockResolvedValue([{ result: AuthorizeResult.DENY }]);

    const response = await request(app).get(
      `/application/by-entity?entityRef=${stringifyEntityRef(
        mockedCatalogEntity,
      )}`,
    );

    expect(response.text).toContain("NotAllowedError: User is unauthorized.");
  });
});

describe("GET /application/by-arn", () => {
  it("should return 200 status for valid request", async () => {
    const response = await request(app).get(
      `/application/by-arn?arn=${mockedApplicationArn}`,
    );

    expect(response.status).toEqual(200);
    expect(response.body).toEqual(mockedAcdpMetricsApi.mockedApplication);
  });

  it("should return 400 status for invalid request", async () => {
    const response = await request(app).get(
      `/application/by-arn?arb=invalid-application-arn`,
    );

    expect(response.status).toEqual(400);
  });

  it("should return NotAllowedError for unauthorized request", async () => {
    jest
      .spyOn(permissions, "authorize")
      .mockResolvedValue([{ result: AuthorizeResult.DENY }]);

    const response = await request(app).get(
      `/application/by-arn?arn=${mockedApplicationArn}`,
    );

    expect(response.text).toContain("NotAllowedError: User is unauthorized.");
  });
});

describe("GET /cost/current-month-net-unblended", () => {
  it("should return 200 status for valid request", async () => {
    const response = await request(app).get(
      `/cost/current-month-net-unblended?entityRef=${stringifyEntityRef(
        mockedCatalogEntity,
      )}&awsApplicationTag=${mockedApplicationTag}`,
    );

    expect(response.status).toEqual(200);
    expect(response.body).toEqual(mockedCurrentMonthCost);
  });

  it("should return 400 status for invalid request", async () => {
    const response = await request(app).get(
      `/cost/current-month-net-unblended?entityRef=${stringifyEntityRef(
        mockedCatalogEntity,
      )}`,
    );

    expect(response.status).toEqual(400);
  });

  it("should return NotAllowedError for unauthorized request", async () => {
    jest
      .spyOn(permissions, "authorize")
      .mockResolvedValue([{ result: AuthorizeResult.DENY }]);

    const response = await request(app).get(
      `/cost/current-month-net-unblended?entityRef=${stringifyEntityRef(
        mockedCatalogEntity,
      )}&awsApplicationTag=${mockedApplicationTag}`,
    );

    expect(response.text).toContain("NotAllowedError: User is unauthorized.");
  });
});
