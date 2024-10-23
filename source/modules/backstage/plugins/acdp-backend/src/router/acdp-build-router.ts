// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express from "express";
import { Logger } from "winston";

import { AuthService, HttpAuthService } from "@backstage/backend-plugin-api";

import { createAcdpBaseRouter, getAuthToken } from "./acdp-base-router";
import { AcdpBuildApi } from "../api";
import { startBuildInputSchema, isValidEntityRef } from "../utils";

interface AcdpBuildRouterOptions {
  logger: Logger;
  acdpBuildApi: AcdpBuildApi;
  auth: AuthService;
  httpAuth: HttpAuthService;
}

export async function createAcdpBuildRouter(
  options: AcdpBuildRouterOptions,
): Promise<express.Router> {
  const { logger, acdpBuildApi, httpAuth, auth } = options;

  const router = await createAcdpBaseRouter({
    logger: logger,
  });

  router.get("/project", async (req, res) => {
    const token = await getAuthToken(httpAuth, auth, req, "catalog");

    const entityRef = req.query.entityRef?.toString() ?? "";

    if (!isValidEntityRef(entityRef)) {
      res.status(400).json({ error: "Missing entityRef" });
      return;
    }

    const entity = await acdpBuildApi.getEntity(entityRef, token);
    const response = await acdpBuildApi.getProject(entity);

    res.status(200).json(response);
  });

  router.get("/builds", async (req, res) => {
    const token = await getAuthToken(httpAuth, auth, req, "catalog");

    const entityRef = req.query.entityRef?.toString() ?? "";

    if (!isValidEntityRef(entityRef)) {
      res.status(400).json({ error: "Missing entityRef" });
      return;
    }

    const entity = await acdpBuildApi.getEntity(entityRef, token);
    const response = await acdpBuildApi.getBuilds(entity);

    res.status(200).json(response);
  });

  router.post("/start-build", async (req, res) => {
    const token = await getAuthToken(httpAuth, auth, req, "catalog");

    const parsedBody = startBuildInputSchema.safeParse(req.body);
    if (!parsedBody.success) {
      logger.error(parsedBody.error.errors);
      return res.status(400).json({ error: parsedBody.error.errors });
    }

    const entity = await acdpBuildApi.getEntity(
      parsedBody.data.entityRef,
      token,
    );
    const response = await acdpBuildApi.startBuild(
      entity,
      parsedBody.data.action,
    );

    return res.status(200).json(response);
  });

  return router;
}
