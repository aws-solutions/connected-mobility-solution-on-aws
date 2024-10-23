// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { createDevApp } from "@backstage/dev-utils";
import {
  acdpPartnerOfferingPlugin,
  AcdpPartnerOfferingPage,
} from "../src/plugin";

createDevApp()
  .registerPlugin(acdpPartnerOfferingPlugin)
  .addPage({
    element: <AcdpPartnerOfferingPage />,
    title: "Root Page",
    path: "/acdp-partner-offering",
  })
  .render();
