// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { createDevApp } from "@backstage/dev-utils";
import {
  acdpPlugin,
  EntityAcdpBuildProjectOverviewCard,
  EntityApplicationsDashboardLinkCard,
} from "../src/plugin";

createDevApp()
  .registerPlugin(acdpPlugin)
  .addPage({
    element: <EntityAcdpBuildProjectOverviewCard />,
    title: "ACDP Build Project Overview Card",
    path: "/acdp-build-project",
  })
  .addPage({
    element: <EntityApplicationsDashboardLinkCard />,
    title: "Applications Dashboard Link Card",
    path: "/acdp-applications-dashboard",
  })
  .render();
