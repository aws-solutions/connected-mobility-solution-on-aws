// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  coreServices,
  createBackendModule,
} from "@backstage/backend-plugin-api";
import { CatalogClient } from "@backstage/catalog-client";
import { ConfigSources } from "@backstage/config-loader";
import { ScmIntegrations } from "@backstage/integration";
import { scaffolderActionsExtensionPoint } from "@backstage/plugin-scaffolder-node/alpha";

import {
  createAcdpCatalogCreateAction,
  createAcdpConfigureAction,
} from "backstage-plugin-acdp-backend";

export const scaffolderModuleAcdpActions = createBackendModule({
  pluginId: "scaffolder", // name of the plugin that the module is targeting
  moduleId: "acdp-actions",
  register(env) {
    env.registerInit({
      deps: {
        scaffolder: scaffolderActionsExtensionPoint,
        reader: coreServices.urlReader,
        discovery: coreServices.discovery,
        auth: coreServices.auth,
        logger: coreServices.logger,
      },
      async init({ scaffolder, reader, discovery, auth, logger }) {
        const configSource = ConfigSources.default({
          argv: process.argv,
          env: process.env,
        });
        const config = await ConfigSources.toConfig(configSource);
        const catalogClient = new CatalogClient({ discoveryApi: discovery });
        const integrations = ScmIntegrations.fromConfig(config);
        scaffolder.addActions(
          await createAcdpConfigureAction({
            config: config,
            reader: reader,
            integrations: integrations,
            catalogClient: catalogClient,
            auth: auth,
            logger: logger,
          }),
          await createAcdpCatalogCreateAction({
            config: config,
            reader: reader,
            integrations: integrations,
            catalogClient: catalogClient,
            auth: auth,
            logger: logger,
            discovery: discovery,
          }),
        );
      },
    });
  },
});
