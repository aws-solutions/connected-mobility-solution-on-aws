// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Route } from "react-router-dom";

import { apiDocsPlugin, ApiExplorerPage } from "@backstage/plugin-api-docs";
import {
  CatalogEntityPage,
  CatalogIndexPage,
  catalogPlugin,
} from "@backstage/plugin-catalog";
import {
  CatalogImportPage,
  catalogImportPlugin,
} from "@backstage/plugin-catalog-import";
import { ScaffolderPage, scaffolderPlugin } from "@backstage/plugin-scaffolder";
import { orgPlugin } from "@backstage/plugin-org";
import { SearchPage } from "@backstage/plugin-search";
import {
  TechDocsIndexPage,
  techdocsPlugin,
  TechDocsReaderPage,
} from "@backstage/plugin-techdocs";
import { TechDocsAddons } from "@backstage/plugin-techdocs-react";
import { ReportIssue } from "@backstage/plugin-techdocs-module-addons-contrib";
import { UserSettingsPage } from "@backstage/plugin-user-settings";
import { HomepageCompositionRoot } from "@backstage/plugin-home";
import {
  AlertDisplay,
  OAuthRequestDialog,
  SignInPage,
} from "@backstage/core-components";
import { createApp } from "@backstage/app-defaults";
import { AppRouter, FlatRoutes } from "@backstage/core-app-api";
import { CatalogGraphPage } from "@backstage/plugin-catalog-graph";
import { RequirePermission } from "@backstage/plugin-permission-react";
import { catalogEntityCreatePermission } from "@backstage/plugin-catalog-common/alpha";
import { useApi, configApiRef } from "@backstage/core-plugin-api";

import { apis } from "./apis/apis";
import { oauth2ApiRef } from "./apis/oauth2Api";
import { Root } from "./components/Root";
import { entityPage } from "./components/EntityPage";
import { searchPage } from "./components/SearchPage";
import { homePage } from "./components/HomePage";

import { AcdpPartnerOfferingPage } from "backstage-plugin-acdp-partner-offering";

const app = createApp({
  apis,
  components: {
    SignInPage: (props) => {
      const configApi = useApi(configApiRef);
      return (
        <>
          {configApi.getString("auth.environment") === "development" ? (
            <SignInPage
              {...props}
              providers={[
                "guest",
                {
                  id: "oauth2",
                  title: "OAuth 2.0 Provider",
                  message: "Sign in using your OAuth 2.0 Provider",
                  apiRef: oauth2ApiRef,
                },
              ]}
            />
          ) : (
            <SignInPage
              {...props}
              auto
              provider={{
                id: "oauth2",
                title: "OAuth 2.0 Provider",
                message: "Sign in using your OAuth 2.0 Provider",
                apiRef: oauth2ApiRef,
              }}
            />
          )}
        </>
      );
    },
  },
  bindRoutes({ bind }) {
    bind(catalogPlugin.externalRoutes, {
      createComponent: scaffolderPlugin.routes.root,
      viewTechDoc: techdocsPlugin.routes.docRoot,
    });
    bind(apiDocsPlugin.externalRoutes, {
      registerApi: catalogImportPlugin.routes.importPage,
    });
    bind(scaffolderPlugin.externalRoutes, {
      registerComponent: catalogImportPlugin.routes.importPage,
    });
    bind(orgPlugin.externalRoutes, {
      catalogIndex: catalogPlugin.routes.catalogIndex,
    });
  },
});

// Backstage requires all extenensions to be part of a single React element tree, for this reason, we opt to use React.JSX.Element types directly
// rather than functional components (e.g. {homePage} vs <HomePage />). Naming conventions are used appropriately to match this style.
// See documentation: https://backstage.io/docs/plugins/composability/#using-extensions-in-an-app
const routes = (
  <FlatRoutes>
    <Route path="/" element={<HomepageCompositionRoot />}>
      {homePage}
    </Route>
    <Route path="/catalog" element={<CatalogIndexPage />} />
    <Route
      path="/catalog/:namespace/:kind/:name"
      element={<CatalogEntityPage />}
    >
      {entityPage}
    </Route>
    <Route path="/docs" element={<TechDocsIndexPage />} />
    <Route
      path="/docs/:namespace/:kind/:name/*"
      element={<TechDocsReaderPage />}
    >
      <TechDocsAddons>
        <ReportIssue />
      </TechDocsAddons>
    </Route>
    <Route path="/create" element={<ScaffolderPage />} />
    <Route path="/partners" element={<AcdpPartnerOfferingPage />} />
    <Route path="/api-docs" element={<ApiExplorerPage />} />
    <Route
      path="/catalog-import"
      element={
        <RequirePermission permission={catalogEntityCreatePermission}>
          <CatalogImportPage />
        </RequirePermission>
      }
    />
    <Route path="/search" element={<SearchPage />}>
      {searchPage}
    </Route>
    <Route path="/settings" element={<UserSettingsPage />} />
    <Route path="/catalog-graph" element={<CatalogGraphPage />} />
  </FlatRoutes>
);

export default app.createRoot(
  <>
    <AlertDisplay />
    <OAuthRequestDialog />
    <AppRouter>
      <Root>{routes}</Root>
    </AppRouter>
  </>,
);
