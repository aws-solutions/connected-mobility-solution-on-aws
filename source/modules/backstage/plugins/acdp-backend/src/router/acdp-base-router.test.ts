// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express, { NextFunction, Request, Response } from "express";
import request from "supertest";

import { mockServices } from "@backstage/backend-test-utils";

import { createAcdpBaseRouter } from ".";
import { resetUrlReaderMocks } from "../mocks";

let app: express.Express;
const mockIsAuthenticated = (req: Request, _: Response, next: NextFunction) => {
  req.user = { token: "test-token" };
  return next();
};

beforeAll(async () => {
  const logger = mockServices.logger.mock();

  const router = await createAcdpBaseRouter({
    logger: logger,
  });

  app = express().use(mockIsAuthenticated, router);
});

beforeEach(() => {
  resetUrlReaderMocks();
});

describe("GET /health", () => {
  it("returns ok", async () => {
    const response = await request(app).get("/health");

    expect(response.status).toEqual(200);
    expect(response.body).toEqual({ status: "ok" });
  });
});
