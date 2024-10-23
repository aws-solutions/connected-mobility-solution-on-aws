// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express from "express";
import Router from "express-promise-router";
import { Logger } from "winston";

import { AuthService, HttpAuthService } from "@backstage/backend-plugin-api";

export interface AcdpBaseRouterOptions {
  logger: Logger;
}

export async function createAcdpBaseRouter(
  options: AcdpBaseRouterOptions,
): Promise<express.Router> {
  const { logger } = options;

  const router = Router();
  router.use(express.json());

  router.get("/health", (_, response) => {
    logger.info("PONG!");
    response.json({ status: "ok" });
  });

  return router;
}

export async function getAuthToken(
  httpAuth: HttpAuthService,
  auth: AuthService,
  req: express.Request<any, any, any, any, any>,
  targetPluginId: string,
): Promise<string> {
  const credentials = await httpAuth.credentials(req);
  const { token } = await auth.getPluginRequestToken({
    onBehalfOf: credentials,
    targetPluginId: targetPluginId,
  });

  return token;
}
