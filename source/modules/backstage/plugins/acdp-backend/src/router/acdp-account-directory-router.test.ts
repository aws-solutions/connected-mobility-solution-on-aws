// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express from "express";
import request from "supertest";
import { mockServices } from "@backstage/backend-test-utils";
import { createAcdpAccountDirectoryRouter } from ".";
import { MockedAcdpAccountDirectoryApi } from "../api/mocks";
import { MockedAcdpAccountDirectoryService } from "../service/mocks";

let mockedAcdpAccountDirectoryService: MockedAcdpAccountDirectoryService;
let mockedAcdpAccountDirectoryApi: MockedAcdpAccountDirectoryApi;
let app: express.Express;

beforeEach(async () => {
  mockedAcdpAccountDirectoryService = new MockedAcdpAccountDirectoryService();
  mockedAcdpAccountDirectoryApi = new MockedAcdpAccountDirectoryApi(
    mockedAcdpAccountDirectoryService,
  );

  const router = await createAcdpAccountDirectoryRouter({
    logger: mockServices.logger.mock(),
    acdpAccountDirectoryApi: mockedAcdpAccountDirectoryApi,
    auth: mockServices.auth(),
    httpAuth: mockServices.httpAuth(),
  });

  app = express().use(router);
});

describe("GET /account-directory/available-accounts-for-all-orgs", () => {
  it("should return 200 status with available accounts", async () => {
    const mockAccounts = [
      { awsAccountId: "123456789012", alias: "Account1" },
      { awsAccountId: "987654321098", alias: "Account2" },
    ];

    jest
      .spyOn(mockedAcdpAccountDirectoryApi, "getAvailableAccounts")
      .mockResolvedValue(mockAccounts);

    const response = await request(app).get(
      "/account-directory/available-accounts-for-all-orgs",
    );

    expect(response.status).toEqual(200);
    expect(response.body).toEqual(mockAccounts);
  });
});

describe("GET /account-directory/available-regions", () => {
  it("should return 200 status with available regions", async () => {
    const mockRegions = ["us-east-1", "us-west-2"];

    jest
      .spyOn(mockedAcdpAccountDirectoryApi, "getAvailableRegions")
      .mockResolvedValue(mockRegions);

    const response = await request(app).get(
      "/account-directory/available-regions",
    );

    expect(response.status).toEqual(200);
    expect(response.body).toEqual(mockRegions);
  });
});
