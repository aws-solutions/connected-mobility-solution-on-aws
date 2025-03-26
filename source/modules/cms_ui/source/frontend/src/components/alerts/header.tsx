// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { HelpPanel, Header } from "@cloudscape-design/components";
import { ExternalLinkGroup, InfoLink, useHelpPanel } from "../commons";

export function AlertsMainInfo() {
  return (
    <HelpPanel
      header={<h2>Fleet</h2>}
      footer={
        <ExternalLinkGroup
          items={[{ href: "#", text: "User Guide for CMS" }]}
        />
      }
    >
      <p>View fleet alerts...TODO</p>
    </HelpPanel>
  );
}

export function DashboardHeader({ actions }: { actions: React.ReactNode }) {
  const loadHelpPanelContent = useHelpPanel();
  return (
    <Header
      variant="h1"
      info={
        <InfoLink onFollow={() => loadHelpPanelContent(<AlertsMainInfo />)} />
      }
      actions={actions}
    >
      Vehicle Dashboard
    </Header>
  );
}
