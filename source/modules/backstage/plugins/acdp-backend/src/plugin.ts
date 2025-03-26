// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  coreServices,
  createBackendPlugin,
} from "@backstage/backend-plugin-api";
import { DefaultAwsCredentialsManager } from "@backstage/integration-aws-node";
import {
  createAcdpBuildRouter,
  createAcdpMetricsRouter,
  AcdpBuildApi,
  AcdpBuildService,
  AcdpMetricsService,
  AcdpMetricsApi,
  createAcdpBaseRouter,
  AcdpAccountDirectoryService,
  AcdpAccountDirectoryApi,
  createAcdpAccountDirectoryRouter,
} from "backstage-plugin-acdp-backend";
import { CatalogClient } from "@backstage/catalog-client";
import { ScmIntegrations } from "@backstage/integration";
import { OperationalMetrics } from "./utils/operational-metrics";

export const acdpPlugin = createBackendPlugin({
  pluginId: "acdp",
  register(env) {
    env.registerInit({
      deps: {
        logger: coreServices.logger,
        config: coreServices.rootConfig,
        discovery: coreServices.discovery,
        httpRouter: coreServices.httpRouter,
        reader: coreServices.urlReader,
        auth: coreServices.auth,
        httpAuth: coreServices.httpAuth,
        permissions: coreServices.permissions,
      },
      async init({
        config,
        logger,
        discovery,
        reader,
        httpRouter,
        auth,
        httpAuth,
        permissions,
      }) {
        logger.info("Initializing the acdp backend plugin.");

        const credsManager = DefaultAwsCredentialsManager.fromConfig(config);
        const catalogClient = new CatalogClient({
          discoveryApi: discovery,
        });

        const integrations = ScmIntegrations.fromConfig(config);

        // ACDP Base
        httpRouter.use(
          await createAcdpBaseRouter({
            logger: logger,
          }),
        );

        // ACDP Build
        const acdpBuildService = new AcdpBuildService({
          config: config,
          reader: reader,
          integrations: integrations,
          awsCredentialsProvider: await credsManager.getCredentialProvider(),
          logger: logger,
          operationalMetrics: new OperationalMetrics({
            logger,
            config,
          }),
        });
        const acdpBuildApi = new AcdpBuildApi(catalogClient, acdpBuildService);
        httpRouter.use(
          await createAcdpBuildRouter({
            logger: logger,
            acdpBuildApi: acdpBuildApi,
            auth: auth,
            httpAuth: httpAuth,
            permissions: permissions,
          }),
        );

        // ACDP Metrics
        const acdpMetricsService = new AcdpMetricsService({
          config: config,
          awsCredentialsProvider: await credsManager.getCredentialProvider(),
          logger: logger,
        });
        const acdpMetricsApi = new AcdpMetricsApi(
          catalogClient,
          acdpMetricsService,
        );
        httpRouter.use(
          await createAcdpMetricsRouter({
            acdpMetricsApi: acdpMetricsApi,
            auth: auth,
            httpAuth: httpAuth,
            permissions: permissions,
          }),
        );

        // ACDP Account-Directory
        const acdpAccountDirectoryService = new AcdpAccountDirectoryService({
          config: config,
          awsCredentialsProvider: await credsManager.getCredentialProvider(),
          logger: logger,
        });
        const acdpAccountDirectoryApi = new AcdpAccountDirectoryApi(
          acdpAccountDirectoryService,
        );
        httpRouter.use(
          await createAcdpAccountDirectoryRouter({
            logger: logger,
            acdpAccountDirectoryApi: acdpAccountDirectoryApi,
            auth: auth,
            httpAuth: httpAuth,
          }),
        );

        httpRouter.addAuthPolicy({
          path: "/health",
          allow: "unauthenticated",
        });
      },
    });
  },
});
