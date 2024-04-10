// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Router } from "express";
import type { PluginEnvironment } from "../types";
import {
  createBuiltinActions,
  createRouter,
} from "@backstage/plugin-scaffolder-backend";
import {
  createAcdpConfigureAction,
  createAcdpCatalogCreateAction,
  createNewYamlFileAction,
} from "backstage-plugin-acdp-backend";

export default async function createPlugin(
  env: PluginEnvironment,
): Promise<Router> {
  const builtInActions = createBuiltinActions({
    catalogClient: env.catalogClient,
    config: env.config,
    integrations: env.integrations,
    reader: env.reader,
  });

  const actions = [
    ...builtInActions,
    await createAcdpCatalogCreateAction({
      config: env.config,
      reader: env.reader,
      integrations: env.integrations,
      catalogClient: env.catalogClient,
      discovery: env.discovery,
      tokenManager: env.tokenManager,
      logger: env.logger,
    }),
    await createAcdpConfigureAction({
      config: env.config,
      reader: env.reader,
      integrations: env.integrations,
      catalogClient: env.catalogClient,
      tokenManager: env.tokenManager,
      logger: env.logger,
    }),
    createNewYamlFileAction(),
  ];

  return await createRouter({
    logger: env.logger,
    config: env.config,
    database: env.database,
    reader: env.reader,
    catalogClient: env.catalogClient,
    actions: actions,
    identity: env.identity,
    permissions: env.permissions,
    auth: env.auth,
    httpAuth: env.httpAuth,
  });
}
