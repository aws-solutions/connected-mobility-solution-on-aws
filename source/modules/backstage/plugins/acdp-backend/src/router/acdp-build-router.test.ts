// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express, { NextFunction, Request, Response } from "express";
import request from "supertest";

import { getVoidLogger } from "@backstage/backend-common";
import { mockServices } from "@backstage/backend-test-utils";
import { stringifyEntityRef } from "@backstage/catalog-model";

import { createAcdpBuildRouter } from ".";
import { StartBuildInput } from "../utils";
import { MockedAcdpBuildService } from "../service/mocks";
import { MockedAcdpBuildApi } from "../api/mocks";
import {
  mockCatalogClient,
  mockedCatalogEntity,
  resetUrlReaderMocks,
} from "../mocks";

import { AcdpBuildAction } from "backstage-plugin-acdp-common";

let app: express.Express;
const mockIsAuthenticated = (req: Request, _: Response, next: NextFunction) => {
  req.user = { token: "test-token" };
  return next();
};

beforeAll(async () => {
  const logger = getVoidLogger();

  const acdpBuildService = new MockedAcdpBuildService();
  const router = await createAcdpBuildRouter({
    logger: logger,
    acdpBuildApi: new MockedAcdpBuildApi(
      mockCatalogClient(mockedCatalogEntity),
      acdpBuildService,
    ),
    auth: mockServices.auth(),
    httpAuth: mockServices.httpAuth(),
  });

  app = express().use(mockIsAuthenticated, router);
});

beforeEach(() => {
  resetUrlReaderMocks();
});

describe("GET /project", () => {
  it("should return 200 status for valid request", async () => {
    const response = await request(app).get(
      `/project?entityRef=${stringifyEntityRef(mockedCatalogEntity)}`,
    );

    expect(response.status).toEqual(200);
  });
});

describe("GET /builds", () => {
  it("should return 200 status for valid request", async () => {
    const response = await request(app).get(
      `/builds?entityRef=${stringifyEntityRef(mockedCatalogEntity)}`,
    );

    expect(response.status).toEqual(200);
  });

  it("should return 400 status for missing entityRef", async () => {
    const response = await request(app).get("/builds");

    expect(response.status).toEqual(400);
  });
});

describe("POST /start-build for deploy", () => {
  it("should return 200 for request with valid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: stringifyEntityRef(mockedCatalogEntity),
      action: AcdpBuildAction.DEPLOY,
    };
    const response = await request(app).post("/start-build").send(requestBody);

    expect(response.status).toEqual(200);
  });

  it("should return 400 for request with invalid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: "bad-value",
      action: AcdpBuildAction.DEPLOY,
    };
    const response = await request(app).post("/start-build").send(requestBody);

    expect(response.status).toEqual(400);
  });
});

describe("POST /start-build for Updates", () => {
  it("should return 200 for request with valid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: stringifyEntityRef(mockedCatalogEntity),
      action: AcdpBuildAction.UPDATE,
    };
    const response = await request(app).post("/start-build").send(requestBody);

    expect(response.status).toEqual(200);
  });

  it("should return 400 for request with invalid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: "bad-value",
      action: AcdpBuildAction.UPDATE,
    };
    const response = await request(app).post("/start-build").send(requestBody);

    expect(response.status).toEqual(400);
  });
});

describe("POST /start-build for Teardown", () => {
  it("should return 200 for request with valid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: stringifyEntityRef(mockedCatalogEntity),
      action: AcdpBuildAction.TEARDOWN,
    };
    const response = await request(app).post("/start-build").send(requestBody);

    expect(response.status).toEqual(200);
  });

  it("should return 400 for request with invalid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: "bad-value",
      action: AcdpBuildAction.TEARDOWN,
    };
    const response = await request(app).post("/start-build").send(requestBody);

    expect(response.status).toEqual(400);
  });
});
