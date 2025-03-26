// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState, SetStateAction } from "react";
import { AppLayout } from "@cloudscape-design/components";
import { Navigation } from "@/components/commons";
import { FormFull, FormHeader } from "./components/form";
import { HelpPanel } from "@cloudscape-design/components";
import { ExternalLinkGroup } from "../../commons";
import { UI_ROUTES } from "@/utils/constants";

export function CreateFleetInfoPanel() {
  return (
    <HelpPanel
      header={<h2>Fleet</h2>}
      footer={
        <ExternalLinkGroup
          items={[{ href: "#", text: "User Guide for CMS" }]}
        />
      }
    >
      <p>Create fleet help...TODO</p>
    </HelpPanel>
  );
}

export function CreateFleetPage() {
  const [toolsIndex, setToolsIndex] = useState(0);
  const [toolsOpen, setToolsOpen] = useState(false);

  const loadHelpPanelContent: any = (content: SetStateAction<number>): any => {
    setToolsIndex(content);
    setToolsOpen(true);
  };

  return (
    <AppLayout
      contentType="form"
      content={
        <FormFull
          loadHelpPanelContent={loadHelpPanelContent}
          header={<FormHeader loadHelpPanelContent={loadHelpPanelContent} />}
        />
      }
      navigation={<Navigation activeHref={UI_ROUTES.FLEET_CREATE} />}
      tools={<CreateFleetInfoPanel />}
      toolsOpen={toolsOpen}
      onToolsChange={({ detail }) => setToolsOpen(detail.open)}
    />
  );
}
