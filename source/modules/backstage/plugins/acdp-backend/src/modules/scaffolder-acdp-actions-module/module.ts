// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { scaffolderActionsExtensionPoint } from "@backstage/plugin-scaffolder-node/alpha";
import {
  createAcdpCatalogCreateAction,
  createAcdpConfigureAction,
} from "backstage-plugin-acdp-backend";
import {
  coreServices,
  createBackendModule,
} from "@backstage/backend-plugin-api";
import { ScmIntegrations } from "@backstage/integration";
import {
  getRootLogger,
  loadBackendConfig,
  loggerToWinstonLogger,
} from "@backstage/backend-common";
import { CatalogClient } from "@backstage/catalog-client";

export const scaffolderModuleAcdpActions = createBackendModule({
  pluginId: "scaffolder", // name of the plugin that the module is targeting
  moduleId: "acdp-actions",
  register(env) {
    env.registerInit({
      deps: {
        scaffolder: scaffolderActionsExtensionPoint,
        // config: coreServices.rootConfig,
        reader: coreServices.urlReader,
        discovery: coreServices.discovery,
        auth: coreServices.auth,
        logger: coreServices.logger,
      },
      async init({ scaffolder, reader, discovery, auth, logger }) {
        const config = await loadBackendConfig({
          argv: process.argv,
          logger: getRootLogger(),
        });
        const catalogClient = new CatalogClient({ discoveryApi: discovery });
        const integrations = ScmIntegrations.fromConfig(config);
        scaffolder.addActions(
          await createAcdpConfigureAction({
            config: config,
            reader: reader,
            integrations: integrations,
            catalogClient: catalogClient,
            auth: auth,
            logger: loggerToWinstonLogger(logger),
          }),
          await createAcdpCatalogCreateAction({
            config: config,
            reader: reader,
            integrations: integrations,
            catalogClient: catalogClient,
            auth: auth,
            logger: loggerToWinstonLogger(logger),
            discovery: discovery,
          }),
        );
      },
    });
  },
});
