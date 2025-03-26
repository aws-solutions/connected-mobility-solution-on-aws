// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express from "express";
import Router from "express-promise-router";

import { LoggerService } from "@backstage/backend-plugin-api";
import { createPermissionIntegrationRouter } from "@backstage/plugin-permission-node";
import { acdpPermissions } from "backstage-plugin-acdp-common";

export interface AcdpBaseRouterOptions {
  logger: LoggerService;
}

export async function createAcdpBaseRouter(
  options: AcdpBaseRouterOptions,
): Promise<express.Router> {
  const { logger } = options;

  // eslint-disable-next-line new-cap
  const router = Router();
  router.use(express.json());

  const permissionIntegrationRouter = createPermissionIntegrationRouter({
    permissions: acdpPermissions,
  });

  router.use(permissionIntegrationRouter);

  router.get("/health", (_, response) => {
    logger.info("PONG!");
    response.json({ status: "ok" });
  });

  return router;
}
