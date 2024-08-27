// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Config } from "@backstage/config";
import express from "express";
import Router from "express-promise-router";
import { Logger } from "winston";
import { AcdpBuildApi } from "../api";
import { startBuildInputSchema } from "../utils";
import { AuthService, HttpAuthService } from "@backstage/backend-plugin-api";
import { CatalogClient } from "@backstage/catalog-client";

export interface AcdpRouterOptions {
  logger: Logger;
  config: Config;
  acdpBuildApi: AcdpBuildApi;
  auth: AuthService;
  httpAuth: HttpAuthService;
  catalogClient: CatalogClient;
}

export async function createRouter(
  options: AcdpRouterOptions,
): Promise<express.Router> {
  const { logger, acdpBuildApi, httpAuth, auth } = options;
  const router = Router();
  router.use(express.json());

  router.get("/health", (_, response) => {
    logger.info("PONG!");
    response.json({ status: "ok" });
  });

  router.get("/project", async (req, res) => {
    const credentials = await httpAuth.credentials(req);
    const { token } = await auth.getPluginRequestToken({
      onBehalfOf: credentials,
      targetPluginId: "catalog",
    });

    const entityRef = req.query.entityRef?.toString();

    if (!entityRef || !isValidEntityRef(entityRef)) {
      res.status(400).json({ error: "Missing entityRef" });
      return;
    }

    const entity = await acdpBuildApi.getEntity(entityRef, token);
    const response = await acdpBuildApi.getProject(entity);

    res.status(200).json(response);
  });

  router.get("/builds", async (req, res) => {
    const credentials = await httpAuth.credentials(req);
    const { token } = await auth.getPluginRequestToken({
      onBehalfOf: credentials,
      targetPluginId: "catalog",
    });

    const entityRef = req.query.entityRef?.toString();

    if (!entityRef || !isValidEntityRef(entityRef)) {
      res.status(400).json({ error: "Missing entityRef" });
      return;
    }

    const entity = await acdpBuildApi.getEntity(entityRef, token);
    const response = await acdpBuildApi.getBuilds(entity);

    res.status(200).json(response);
  });

  router.post("/startBuild", async (req, res) => {
    const credentials = await httpAuth.credentials(req);
    const { token } = await auth.getPluginRequestToken({
      onBehalfOf: credentials,
      targetPluginId: "catalog",
    });
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

function isValidEntityRef(input: string): boolean {
  // Define the regex pattern for validating an entityRef
  const entityRefPattern = /^[a-zA-Z0-9-_]+:[a-zA-Z0-9-_]+\/[a-zA-Z0-9-_]+$/;

  // Test the input string against the pattern
  return entityRefPattern.test(input);
}
