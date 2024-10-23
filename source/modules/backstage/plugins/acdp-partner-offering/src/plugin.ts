// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  createPlugin,
  createRoutableExtension,
} from "@backstage/core-plugin-api";

import { rootRouteRef } from "./routes";

export const acdpPartnerOfferingPlugin = createPlugin({
  id: "acdp-partner-offering",
  routes: {
    root: rootRouteRef,
  },
});

// Partner offerings is given a unique route in top-level FlatRoutes component in the Backstage App, requiring a routable extension
// https://backstage.io/docs/plugins/plugin-development#routing
export const AcdpPartnerOfferingPage = acdpPartnerOfferingPlugin.provide(
  createRoutableExtension({
    name: "AcdpPartnerOfferingPage",
    component: () =>
      import("./components/PartnerOfferingList").then(
        (m) => m.PartnerOfferingListPage,
      ),
    mountPoint: rootRouteRef,
  }),
);
