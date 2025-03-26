// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express from "express";
import Router from "express-promise-router";

import {
  AuthService,
  HttpAuthService,
  PermissionsService,
} from "@backstage/backend-plugin-api";
import { NotAllowedError } from "@backstage/errors";
import { AuthorizeResult } from "@backstage/plugin-permission-common";
import { acdpMetricsReadPermission } from "backstage-plugin-acdp-common";

import { AcdpMetricsApi } from "../api";
import { isValidApplicationArn, isValidEntityRef } from "../utils";

interface AcdpMetricsRouterOptions {
  acdpMetricsApi: AcdpMetricsApi;
  auth: AuthService;
  httpAuth: HttpAuthService;
  permissions: PermissionsService;
}

export async function createAcdpMetricsRouter(
  options: AcdpMetricsRouterOptions,
): Promise<express.Router> {
  const { acdpMetricsApi, httpAuth, auth, permissions } = options;

  const router = Router();
  router.use(express.json());

  router.get("/application/by-entity", async (req, res) => {
    const credentials = await httpAuth.credentials(req, { allow: ["user"] });

    const authorizationDecision = (
      await permissions.authorize([{ permission: acdpMetricsReadPermission }], {
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
      res.status(400).json({ error: "Missing or invalid entityRef" });
      return;
    }

    const entity = await acdpMetricsApi.getEntity(entityRef, catalogToken);
    const response = await acdpMetricsApi.getApplicationByEntity(entity);

    res.status(200).json(response);
  });

  router.get("/application/by-arn", async (req, res) => {
    const credentials = await httpAuth.credentials(req, { allow: ["user"] });

    const authorizationDecision = (
      await permissions.authorize([{ permission: acdpMetricsReadPermission }], {
        credentials,
      })
    )[0];

    if (authorizationDecision.result === AuthorizeResult.DENY) {
      throw new NotAllowedError("User is unauthorized.");
    }

    const applicationArn = req.query.arn?.toString() ?? "";

    if (!isValidApplicationArn(applicationArn)) {
      res.status(400).json({ error: "Missing or invalid application arn" });
      return;
    }

    const response = await acdpMetricsApi.getApplicationByArn(applicationArn);

    res.status(200).json(response);
  });

  router.get("/cost/current-month-net-unblended", async (req, res) => {
    const credentials = await httpAuth.credentials(req, { allow: ["user"] });

    const authorizationDecision = (
      await permissions.authorize([{ permission: acdpMetricsReadPermission }], {
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
    const awsApplicationTag = req.query.awsApplicationTag?.toString() ?? "";

    let areQueryParamsValid = true;
    if (!isValidEntityRef(entityRef)) {
      res.status(400).json({ error: "Missing or invalid entityRef" });
      areQueryParamsValid = false;
    } else if (awsApplicationTag === "") {
      res.status(400).json({ error: "Missing awsApplicationTag" });
      areQueryParamsValid = false;
    }

    if (!areQueryParamsValid) return;

    const entity = await acdpMetricsApi.getEntity(entityRef, catalogToken);
    const response = await acdpMetricsApi.getNetUnblendedCurrentMonthCost(
      entity,
      awsApplicationTag,
    );

    res.status(200).json(response);
  });

  return router;
}
