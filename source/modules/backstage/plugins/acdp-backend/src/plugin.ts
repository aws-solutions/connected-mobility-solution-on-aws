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
} from "backstage-plugin-acdp-backend";
import { loggerToWinstonLogger } from "@backstage/backend-common";
import { CatalogClient } from "@backstage/catalog-client";
import { ScmIntegrations } from "@backstage/integration";

export const acdpPlugin = createBackendPlugin({
  pluginId: "acdp-backend",
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
      },
      async init({
        config,
        logger,
        discovery,
        reader,
        httpRouter,
        auth,
        httpAuth,
      }) {
        const winstonLogger = loggerToWinstonLogger(logger);
        const credsManager = DefaultAwsCredentialsManager.fromConfig(config);
        const catalogClient = new CatalogClient({
          discoveryApi: discovery,
        });

        const integrations = ScmIntegrations.fromConfig(config);

        // ACDP Build
        const acdpBuildService = new AcdpBuildService({
          config: config,
          reader: reader,
          integrations: integrations,
          awsCredentialsProvider: await credsManager.getCredentialProvider(),
          logger: winstonLogger,
        });
        const acdpBuildApi = new AcdpBuildApi(catalogClient, acdpBuildService);
        httpRouter.use(
          await createAcdpBuildRouter({
            logger: winstonLogger,
            acdpBuildApi: acdpBuildApi,
            auth: auth,
            httpAuth: httpAuth,
          }),
        );

        // ACDP Metrics
        const acdpMetricsService = new AcdpMetricsService({
          config: config,
          awsCredentialsProvider: await credsManager.getCredentialProvider(),
          logger: winstonLogger,
        });
        const acdpMetricsApi = new AcdpMetricsApi(
          catalogClient,
          acdpMetricsService,
        );
        httpRouter.use(
          await createAcdpMetricsRouter({
            logger: winstonLogger,
            acdpMetricsApi: acdpMetricsApi,
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
