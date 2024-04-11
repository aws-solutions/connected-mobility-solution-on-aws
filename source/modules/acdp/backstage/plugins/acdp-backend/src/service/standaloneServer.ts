// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  HostDiscovery,
  UrlReaders,
  createServiceBuilder,
  loadBackendConfig,
} from "@backstage/backend-common";
import { Server } from "http";
import { Logger } from "winston";
import { createRouter } from "./router";
import { DefaultAwsCredentialsManager } from "@backstage/integration-aws-node";
import { AcdpBuildApi } from "backstage-plugin-acdp-backend";
import { AcdpBuildService } from "./acdp-build-service";
import { ScmIntegrations } from "@backstage/integration";
import { CatalogClient } from "@backstage/catalog-client";

export interface ServerOptions {
  port: number;
  enableCors: boolean;
  logger: Logger;
}

export async function startStandaloneServer(
  options: ServerOptions,
): Promise<Server> {
  const logger = options.logger.child({ service: "acdp-backend" });
  const config = await loadBackendConfig({
    argv: process.argv,
    logger: logger,
  });
  const integrations = ScmIntegrations.fromConfig(config);
  const credsManager = DefaultAwsCredentialsManager.fromConfig(config);
  const discovery = HostDiscovery.fromConfig(config);
  const urlReader = UrlReaders.default({ logger: logger, config: config });
  const catalogClient = new CatalogClient({
    discoveryApi: discovery,
  });

  const acdpBuildService = new AcdpBuildService({
    config: config,
    reader: urlReader,
    integrations: integrations,
    awsCredentialsProvider: await credsManager.getCredentialProvider(),
    logger: logger,
  });
  const acdpBuildApi = new AcdpBuildApi(catalogClient, acdpBuildService);

  logger.debug("Starting application server...");
  const router = await createRouter({
    logger,
    config: config,
    acdpBuildApi: acdpBuildApi,
  });

  let service = createServiceBuilder(module)
    .setPort(options.port)
    .addRouter("/acdp", router);
  if (options.enableCors) {
    service = service.enableCors({ origin: "http://localhost:3000" });
  }

  return await service.start().catch((err) => {
    logger.error(err);
    process.exit(1);
  });
}

module.hot?.accept();
