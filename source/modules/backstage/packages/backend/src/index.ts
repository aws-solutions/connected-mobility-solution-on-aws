// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import authPlugin from "@backstage/plugin-auth-backend";
import authModuleGuestProvider from "@backstage/plugin-auth-backend-module-guest-provider";
import appPlugin from "@backstage/plugin-app-backend/alpha";
import catalogPlugin from "@backstage/plugin-catalog-backend/alpha";
import catalogModuleAwsS3EntityProvider from "@backstage/plugin-catalog-backend-module-aws/alpha";
import catalogModuleScaffolderEntityModel from "@backstage/plugin-catalog-backend-module-scaffolder-entity-model";
import { createBackend } from "@backstage/backend-defaults";
import { rootHttpRouterServiceFactory } from "@backstage/backend-defaults/rootHttpRouter";
import scaffolderPlugin from "@backstage/plugin-scaffolder-backend/alpha";
import techdocsPlugin from "@backstage/plugin-techdocs-backend/alpha";
import proxyPlugin from "@backstage/plugin-proxy-backend/alpha";
import searchPlugin from "@backstage/plugin-search-backend/alpha";
import searchTechdocsCollator from "@backstage/plugin-search-backend-module-techdocs/alpha";
import searchCatalogCollator from "@backstage/plugin-search-backend-module-catalog/alpha";

import acdpPlugin, {
  scaffolderModuleAcdpActions,
} from "backstage-plugin-acdp-backend";
import acdpPartnerOfferingPlugin from "backstage-plugin-acdp-partner-offering-backend";

import authModuleOAuth2Provider from "auth-oauth2-provider-module";
import techdocsModuleCustomBuildStrategy from "techdocs-custom-build-strategy-module";

import { customErrorHandler } from "./middleware";

const backend = createBackend();

// Auth
backend.add(authPlugin);
backend.add(authModuleGuestProvider);
backend.add(authModuleOAuth2Provider);

// Frontend / App
backend.add(appPlugin);

// Catalog
backend.add(catalogPlugin);
backend.add(catalogModuleAwsS3EntityProvider);
backend.add(catalogModuleScaffolderEntityModel);

// Scaffolder
backend.add(scaffolderPlugin);
backend.add(scaffolderModuleAcdpActions);

// Techdocs
backend.add(techdocsPlugin);
backend.add(techdocsModuleCustomBuildStrategy);

// Proxy
backend.add(proxyPlugin);

// Search
backend.add(searchPlugin);
backend.add(searchTechdocsCollator);
backend.add(searchCatalogCollator);

// ACDP
backend.add(acdpPlugin);

// ACDP Partner Offering
backend.add(acdpPartnerOfferingPlugin);

// Customize the root http router to insert custom error handling middleware which strips the "cause" from the express response
// Backstage Documentation: https://backstage.io/docs/backend-system/core-services/root-http-router#configuring-the-service
backend.add(
  rootHttpRouterServiceFactory({
    // Provide all built-in middleware, excluding error. Then replace error with a custom error handler.
    configure: ({ app, config, logger, middleware, routes }) => {
      // Default middleware
      app.use(middleware.helmet());
      app.use(middleware.cors());
      app.use(middleware.compression());
      app.use(middleware.logging());

      // Routes registered by other plugins
      app.use(routes);

      // Default middleware required after routes
      app.use(middleware.notFound());

      app.use(
        customErrorHandler(
          {
            config: config,
            logger: logger,
          },
          {
            showStackTraces: false,
          },
        ),
      );
    },
  }),
);

backend.start();
