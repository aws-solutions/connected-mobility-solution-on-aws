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
import { acdpBuildApiRef, AcdpBuildApi } from "./api";
import { AcdpBuildWidget } from "./components/CodeBuildWidget";

import { rootRouteRef } from "./routes";

export const acdpPlugin: BackstagePlugin = createPlugin({
  id: "acdp",
  apis: [
    createApiFactory({
      api: acdpBuildApiRef,
      deps: { configApi: configApiRef, identityApi: identityApiRef },
      factory: ({ configApi, identityApi }) =>
        new AcdpBuildApi({ configApi, identityApi }),
    }),
  ],
  routes: {
    entityContent: rootRouteRef,
  },
});

export const EntityAcdpBuildProjectOverviewCard = acdpPlugin.provide(
  createComponentExtension({
    name: "EntityAcdpBuildCard",
    component: {
      sync: AcdpBuildWidget,
    },
  }),
);
