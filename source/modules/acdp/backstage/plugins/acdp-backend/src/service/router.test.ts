// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { getVoidLogger } from "@backstage/backend-common";
import express, { NextFunction, Request, Response } from "express";
import request from "supertest";

import { createRouter } from "./router";
import { AcdpBuildApi } from "../api/acdp-build-api";
import { StartBuildInput } from "../utils";
import { Entity, stringifyEntityRef } from "@backstage/catalog-model";
import {
  mockCatalogClient,
  mockConfig,
  mockedCatalogEntity,
  resetMocks,
} from "../__mocks__/common-mocks";
import { MockedAcdpBuildService } from "./__mocks__/acdp-build-service.mock";
import { CatalogClient } from "@backstage/catalog-client";
import {
  AcdpBuildAction,
  AcdpBuildProject,
  AcdpBuildProjectBuild,
} from "backstage-plugin-acdp-common";

let app: express.Express;
const mockIsAuthenticated = (req: Request, _: Response, next: NextFunction) => {
  req.user = { token: "test-token" };
  return next();
};

class MockedAcdpBuildApi extends AcdpBuildApi {
  public constructor(
    catalogClient: CatalogClient,
    acdpBuildService: MockedAcdpBuildService,
  ) {
    super(catalogClient, acdpBuildService);
  }

  public getProject(): Promise<AcdpBuildProject> {
    return Promise.resolve({
      name: "test-project",
      arn: "arn:aws:codebuild:us-west2:111111111111:project/test",
      environment: {
        type: "LINUX_CONTAINER",
        image: "aws/codebuild/amazonlinux2-x86_64-standard:3.0",
        computeType: "BUILD_GENERAL1_SMALL",
        privilegedMode: false,
        imagePullCredentialsType: "CODEBUILD",
      },
      created: new Date("2022-05-20T13:58:29.342000-06:00"),
      lastModified: new Date("2022-05-20T13:58:29.342000-06:00"),
    });
  }

  public getBuilds(entity: Entity): Promise<AcdpBuildProjectBuild[]> {
    if (entity === undefined) return Promise.reject();

    return Promise.resolve([
      {
        arn: "arn:aws:codebuild:us-west2:111111111111:build/test:test",
        buildNumber: 1,
        buildStatus: "SUCCEEDED",
        currentPhase: "COMPLETED",
        endTime: new Date("2022-04-14T23:34:38.397Z"),
        startTime: new Date("2022-04-14T23:31:26.086Z"),
      },
      {
        arn: "arn:aws:codebuild:us-west2:111111111111:build/test:test",
        buildComplete: true,
        buildNumber: 2,
        buildStatus: "SUCCEEDED",
        currentPhase: "COMPLETED",
        endTime: new Date("2022-04-14T23:34:38.397Z"),
        startTime: new Date("2022-04-14T23:31:26.086Z"),
      },
    ]);
  }

  public startBuild(entity: Entity): Promise<any> {
    return Promise.resolve(entity);
  }

  public getEntity(
    entityRef: string,
    backstageApiToken: string | undefined,
  ): Promise<Entity> {
    return super.getEntity(entityRef, backstageApiToken);
  }
}

beforeAll(async () => {
  const logger = getVoidLogger();

  const acdpBuildService = new MockedAcdpBuildService();
  const router = await createRouter({
    logger: logger,
    config: mockConfig,
    acdpBuildApi: new MockedAcdpBuildApi(
      mockCatalogClient(mockedCatalogEntity),
      acdpBuildService,
    ),
  });

  app = express().use(mockIsAuthenticated, router);
});

beforeEach(() => {
  resetMocks();
});

describe("GET /health", () => {
  it("returns ok", async () => {
    const response = await request(app).get("/health");

    expect(response.status).toEqual(200);
    expect(response.body).toEqual({ status: "ok" });
  });
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

describe("POST /startBuild for deploy", () => {
  it("should return 200 for request with valid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: stringifyEntityRef(mockedCatalogEntity),
      action: AcdpBuildAction.DEPLOY,
    };
    await request(app).post("/startBuild").send(requestBody).expect(200);
  });

  it("should return 400 for request with invalid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: "bad-value",
      action: AcdpBuildAction.DEPLOY,
    };
    await request(app).post("/startBuild").send(requestBody).expect(400);
  });
});

describe("POST /startBuild for Updates", () => {
  it("should return 200 for request with valid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: stringifyEntityRef(mockedCatalogEntity),
      action: AcdpBuildAction.UPDATE,
    };
    await request(app).post("/startBuild").send(requestBody).expect(200);
  });

  it("should return 400 for request with invalid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: "bad-value",
      action: AcdpBuildAction.UPDATE,
    };
    await request(app).post("/startBuild").send(requestBody).expect(400);
  });
});

describe("POST /startBuild for Teardown", () => {
  it("should return 200 for request with valid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: stringifyEntityRef(mockedCatalogEntity),
      action: AcdpBuildAction.TEARDOWN,
    };
    await request(app).post("/startBuild").send(requestBody).expect(200);
  });

  it("should return 400 for request with invalid json body", async () => {
    const requestBody: StartBuildInput = {
      entityRef: "bad-value",
      action: AcdpBuildAction.TEARDOWN,
    };
    await request(app).post("/startBuild").send(requestBody).expect(400);
  });
});
