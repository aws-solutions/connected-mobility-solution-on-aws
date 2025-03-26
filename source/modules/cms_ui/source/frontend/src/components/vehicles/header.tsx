// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { HelpPanel, Header } from "@cloudscape-design/components";
import { ExternalLinkGroup, InfoLink, useHelpPanel } from "../commons";

export function VehiclesMainInfo() {
  return (
    <HelpPanel
      header={<h2>Vehicle</h2>}
      footer={
        <ExternalLinkGroup
          items={[{ href: "#", text: "User Guide for CMS" }]}
        />
      }
    >
      <p>View vehicle management help...TODO</p>
    </HelpPanel>
  );
}

export function DashboardHeader({ actions }: { actions: React.ReactNode }) {
  const loadHelpPanelContent = useHelpPanel();
  return (
    <Header
      variant="h1"
      info={
        <InfoLink onFollow={() => loadHelpPanelContent(<VehiclesMainInfo />)} />
      }
      actions={actions}
    >
      Vehicle Dashboard
    </Header>
  );
}
