// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import express, { Router } from "express";

import {
  AuthService,
  HttpAuthService,
  LoggerService,
} from "@backstage/backend-plugin-api";

import { AcdpAccountDirectoryApi } from "../api/acdp-account-directory-api";

interface AcdpAccountDirectoryRouterOptions {
  logger: LoggerService;
  acdpAccountDirectoryApi: AcdpAccountDirectoryApi;
  auth: AuthService;
  httpAuth: HttpAuthService;
}

export async function createAcdpAccountDirectoryRouter(
  options: AcdpAccountDirectoryRouterOptions,
): Promise<express.Router> {
  const { acdpAccountDirectoryApi } = options;

  const router = Router();
  router.use(express.json());

  router.get(
    "/account-directory/available-accounts-for-all-orgs",
    async (_, res) => {
      const response = await acdpAccountDirectoryApi.getAvailableAccounts();

      res.status(200).json(response);
    },
  );

  router.get("/account-directory/available-regions", async (_, res) => {
    const response = await acdpAccountDirectoryApi.getAvailableRegions();

    res.status(200).json(response);
  });

  return router;
}
