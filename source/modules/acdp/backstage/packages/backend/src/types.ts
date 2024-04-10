// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Logger } from "winston";
import { Config } from "@backstage/config";
import {
  PluginCacheManager,
  PluginDatabaseManager,
  PluginEndpointDiscovery,
  TokenManager,
  UrlReader,
} from "@backstage/backend-common";
import { PluginTaskScheduler } from "@backstage/backend-tasks";
import { PermissionEvaluator } from "@backstage/plugin-permission-common";
import { IdentityApi } from "@backstage/plugin-auth-node";
import { CatalogClient } from "@backstage/catalog-client";
import { ScmIntegrations } from "@backstage/integration";
import { AuthService, HttpAuthService } from "@backstage/backend-plugin-api";

export type PluginEnvironment = {
  auth: AuthService;
  httpAuth: HttpAuthService;
  logger: Logger;
  database: PluginDatabaseManager;
  cache: PluginCacheManager;
  catalogClient: CatalogClient;
  config: Config;
  discovery: PluginEndpointDiscovery;
  identity: IdentityApi;
  integrations: ScmIntegrations;
  permissions: PermissionEvaluator;
  reader: UrlReader;
  scheduler: PluginTaskScheduler;
  tokenManager: TokenManager;
};
