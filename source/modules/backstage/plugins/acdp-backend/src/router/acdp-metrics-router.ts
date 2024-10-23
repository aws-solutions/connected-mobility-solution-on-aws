// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express from "express";
import { Logger } from "winston";

import { AuthService, HttpAuthService } from "@backstage/backend-plugin-api";

import { createAcdpBaseRouter, getAuthToken } from "./acdp-base-router";
import { AcdpMetricsApi } from "../api";
import { isValidApplicationArn, isValidEntityRef } from "../utils";

interface AcdpMetricsRouterOptions {
  logger: Logger;
  acdpMetricsApi: AcdpMetricsApi;
  auth: AuthService;
  httpAuth: HttpAuthService;
}

export async function createAcdpMetricsRouter(
  options: AcdpMetricsRouterOptions,
): Promise<express.Router> {
  const { logger, acdpMetricsApi, httpAuth, auth } = options;

  const router = await createAcdpBaseRouter({
    logger: logger,
  });

  router.get("/application/by-entity", async (req, res) => {
    const token = await getAuthToken(httpAuth, auth, req, "catalog");

    const entityRef = req.query.entityRef?.toString() ?? "";

    if (!isValidEntityRef(entityRef)) {
      res.status(400).json({ error: "Missing or invalid entityRef" });
      return;
    }

    const entity = await acdpMetricsApi.getEntity(entityRef, token);
    const response = await acdpMetricsApi.getApplicationByEntity(entity);

    res.status(200).json(response);
  });

  router.get("/application/by-arn", async (req, res) => {
    const applicationArn = req.query.arn?.toString() ?? "";

    if (!isValidApplicationArn(applicationArn)) {
      res.status(400).json({ error: "Missing or invalid application arn" });
      return;
    }

    const response = await acdpMetricsApi.getApplicationByArn(applicationArn);

    res.status(200).json(response);
  });

  router.get("/cost/current-month-net-unblended", async (req, res) => {
    const token = await getAuthToken(httpAuth, auth, req, "catalog");

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

    const entity = await acdpMetricsApi.getEntity(entityRef, token);
    const response = await acdpMetricsApi.getNetUnblendedCurrentMonthCost(
      entity,
      awsApplicationTag,
    );

    res.status(200).json(response);
  });

  return router;
}
