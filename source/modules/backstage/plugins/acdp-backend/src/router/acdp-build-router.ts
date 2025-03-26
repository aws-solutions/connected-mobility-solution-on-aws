// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express from "express";
import Router from "express-promise-router";

import {
  AuthService,
  HttpAuthService,
  LoggerService,
  PermissionsService,
} from "@backstage/backend-plugin-api";
import { NotAllowedError } from "@backstage/errors";
import { AuthorizeResult } from "@backstage/plugin-permission-common";
import {
  acdpBuildReadPermission,
  acdpBuildStartPermission,
} from "backstage-plugin-acdp-common";

import { AcdpBuildApi } from "../api";
import { startBuildInputSchema, isValidEntityRef } from "../utils";

interface AcdpBuildRouterOptions {
  logger: LoggerService;
  acdpBuildApi: AcdpBuildApi;
  auth: AuthService;
  httpAuth: HttpAuthService;
  permissions: PermissionsService;
}

export async function createAcdpBuildRouter(
  options: AcdpBuildRouterOptions,
): Promise<express.Router> {
  const { logger, acdpBuildApi, httpAuth, auth, permissions } = options;

  const router = Router();
  router.use(express.json());

  router.get("/project", async (req, res) => {
    const credentials = await httpAuth.credentials(req, { allow: ["user"] });

    const authorizationDecision = (
      await permissions.authorize([{ permission: acdpBuildReadPermission }], {
        credentials,
      })
    )[0];

    if (authorizationDecision.result === AuthorizeResult.DENY) {
      throw new NotAllowedError("User is unauthorized.");
    }

    const entityRef = req.query.entityRef?.toString() ?? "";

    if (!isValidEntityRef(entityRef)) {
      res.status(400).json({ error: "Missing entityRef" });
      return;
    }

    const response = await acdpBuildApi.getProject();

    res.status(200).json(response);
  });

  router.get("/builds", async (req, res) => {
    const credentials = await httpAuth.credentials(req, { allow: ["user"] });

    const authorizationDecision = (
      await permissions.authorize([{ permission: acdpBuildReadPermission }], {
        credentials,
      })
    )[0];

    if (authorizationDecision.result === AuthorizeResult.DENY) {
      throw new NotAllowedError("User is unauthorized.");
    }

    const { token: catalogToken } = await auth.getPluginRequestToken({
      onBehalfOf: credentials,
      targetPluginId: "catalog",
    });

    const entityRef = req.query.entityRef?.toString() ?? "";

    if (!isValidEntityRef(entityRef)) {
      res.status(400).json({ error: "Missing entityRef" });
      return;
    }

    const entity = await acdpBuildApi.getEntity(entityRef, catalogToken);
    const response = await acdpBuildApi.getBuilds(entity);

    res.status(200).json(response);
  });

  router.post("/start-build", async (req, res) => {
    const credentials = await httpAuth.credentials(req, { allow: ["user"] });

    const authorizationDecision = (
      await permissions.authorize([{ permission: acdpBuildStartPermission }], {
        credentials,
      })
    )[0];

    if (authorizationDecision.result === AuthorizeResult.DENY) {
      throw new NotAllowedError("User is unauthorized.");
    }

    const { token: catalogToken } = await auth.getPluginRequestToken({
      onBehalfOf: credentials,
      targetPluginId: "catalog",
    });

    const parsedBody = startBuildInputSchema.safeParse(req.body);
    if (!parsedBody.success) {
      logger.error(parsedBody.error.message);
      return res.status(400).json({ error: parsedBody.error.issues });
    }

    const entity = await acdpBuildApi.getEntity(
      parsedBody.data.entityRef,
      catalogToken,
    );
    const response = await acdpBuildApi.startBuild(
      entity,
      parsedBody.data.action,
    );

    return res.status(200).json(response);
  });

  return router;
}
