// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { PluginEnvironment } from "../types";
import { DefaultAwsCredentialsManager } from "@backstage/integration-aws-node";
import {
  createRouter,
  AcdpBuildApi,
  AcdpBuildService,
} from "backstage-plugin-acdp-backend";
import { CatalogClient } from "@backstage/catalog-client";
import { ScmIntegrations } from "@backstage/integration";

export default async function createPlugin(env: PluginEnvironment) {
  const credsManager = DefaultAwsCredentialsManager.fromConfig(env.config);
  const catalogClient = new CatalogClient({
    discoveryApi: env.discovery,
  });

  const integrations = ScmIntegrations.fromConfig(env.config);

  const acdpBuildService = new AcdpBuildService({
    config: env.config,
    reader: env.reader,
    integrations: integrations,
    awsCredentialsProvider: await credsManager.getCredentialProvider(),
    logger: env.logger,
  });
  const acdpBuildApi = new AcdpBuildApi(catalogClient, acdpBuildService);
  return await createRouter({
    logger: env.logger,
    config: env.config,
    acdpBuildApi: acdpBuildApi,
  });
}
