// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  createApiFactory,
  createComponentExtension,
  createPlugin,
  identityApiRef,
  configApiRef,
  BackstagePlugin,
} from "@backstage/core-plugin-api";

import {
  acdpAccountDirectoryApiRef,
  AcdpAccountDirectoryImpl,
  acdpBuildApiRef,
  AcdpBuildImpl,
  acdpMetricsApiRef,
  AcdpMetricsImpl,
} from "./api";

export const acdpPlugin: BackstagePlugin = createPlugin({
  id: "acdp",
  apis: [
    createApiFactory({
      api: acdpBuildApiRef,
      deps: { configApi: configApiRef, identityApi: identityApiRef },
      factory: ({ configApi, identityApi }) =>
        new AcdpBuildImpl({ configApi, identityApi }),
    }),
    createApiFactory({
      api: acdpMetricsApiRef,
      deps: { configApi: configApiRef, identityApi: identityApiRef },
      factory: ({ configApi, identityApi }) =>
        new AcdpMetricsImpl({ configApi, identityApi }),
    }),
    createApiFactory({
      api: acdpAccountDirectoryApiRef,
      deps: { configApi: configApiRef, identityApi: identityApiRef },
      factory: ({ configApi, identityApi }) =>
        new AcdpAccountDirectoryImpl({ configApi, identityApi }),
    }),
  ],
});

/*
// ACDP plugin extensions are Components added to the existing EntityLayout for the custom EntityPage.
// Routable components are not required for EntityLayout tabs with custom route extensions
//
// Naming patterns for front-end plugin extensions: https://backstage.io/docs/plugins/composability/#naming-patterns
*/
// CI/CD CodeBuild Widget
export const EntityAcdpBuildProjectOverviewCard = acdpPlugin.provide(
  createComponentExtension({
    name: "EntityAcdpBuildProjectOverviewCard",
    component: {
      lazy: () =>
        import("./components/CodeBuildWidget").then(
          (component) => component.AcdpBuildWidget,
        ),
    },
  }),
);

// Metrics myApplications Dashboard Widget
export const EntityApplicationsDashboardLinkCard = acdpPlugin.provide(
  createComponentExtension({
    name: "EntityApplicationsDashboardLinkCard",
    component: {
      lazy: () =>
        import("./components/MyApplicationsWidget").then(
          (component) => component.MyApplicationsWidget,
        ),
    },
  }),
);
