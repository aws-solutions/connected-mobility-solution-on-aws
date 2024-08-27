// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  coreServices,
  createBackendPlugin,
} from "@backstage/backend-plugin-api";
import { DefaultAwsCredentialsManager } from "@backstage/integration-aws-node";
import {
  createRouter,
  AcdpBuildApi,
  AcdpBuildService,
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

        const acdpBuildService = new AcdpBuildService({
          config: config,
          reader: reader,
          integrations: integrations,
          awsCredentialsProvider: await credsManager.getCredentialProvider(),
          logger: winstonLogger,
        });
        const acdpBuildApi = new AcdpBuildApi(catalogClient, acdpBuildService);
        httpRouter.use(
          await createRouter({
            logger: winstonLogger,
            config: config,
            acdpBuildApi: acdpBuildApi,
            auth: auth,
            httpAuth: httpAuth,
            catalogClient: catalogClient,
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
