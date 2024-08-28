// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { createDevApp } from "@backstage/dev-utils";
import { acdpPlugin, EntityAcdpBuildProjectOverviewCard } from "../src/plugin";

createDevApp()
  .registerPlugin(acdpPlugin)
  .addPage({
    element: <EntityAcdpBuildProjectOverviewCard />,
    title: "Root Page",
    path: "/acdp",
  })
  .render();
