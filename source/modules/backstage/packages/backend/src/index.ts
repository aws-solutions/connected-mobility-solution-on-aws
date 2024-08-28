// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Backstage Plugins
import authPlugin from "@backstage/plugin-auth-backend";
import authModuleGuestProvider from "@backstage/plugin-auth-backend-module-guest-provider";
import appPlugin from "@backstage/plugin-app-backend/alpha";
import catalogPlugin from "@backstage/plugin-catalog-backend/alpha";
import catalogModuleAwsS3EntityProvider from "@backstage/plugin-catalog-backend-module-aws/alpha";
import catalogModuleScaffolderEntityModel from "@backstage/plugin-catalog-backend-module-scaffolder-entity-model";
import { createBackend } from "@backstage/backend-defaults";
import scaffolderPlugin from "@backstage/plugin-scaffolder-backend/alpha";
import techdocsPlugin from "@backstage/plugin-techdocs-backend/alpha";
import proxyPlugin from "@backstage/plugin-proxy-backend/alpha";
import searchPlugin from "@backstage/plugin-search-backend/alpha";
import searchTechdocsCollator from "@backstage/plugin-search-backend-module-techdocs/alpha";
import searchCatalogCollator from "@backstage/plugin-search-backend-module-catalog/alpha";

// Custom Modules/Plugins
import authModuleOAuth2Provider from "auth-oauth2-provider-module";
import acdpPlugin, {
  scaffolderModuleAcdpActions,
} from "backstage-plugin-acdp-backend";
import techdocsModuleCustomBuildStrategy from "techdocs-custom-build-strategy-module";

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

backend.start();
