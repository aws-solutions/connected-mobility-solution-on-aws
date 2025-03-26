// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState, useContext, SetStateAction } from "react";
import { AppLayoutProps, AppLayout } from "@cloudscape-design/components";
import { HelpPanelProvider } from "../../commons";
import { Navigation } from "../../commons/common-components";
import { CampaignsMainInfo } from "../header";
import { Content } from "./content";
import { UI_ROUTES } from "@/utils/constants";
import { Breadcrumbs } from "@/components/commons/breadcrumbs";
import {
  CampaignManagementContext,
  CampaignManagementContextProvider,
} from "./CampaignManagementContext";

export default function CampaignManagementView() {
  return (
    <CampaignManagementContextProvider>
      <CampaignManagementViewWithContext />
    </CampaignManagementContextProvider>
  );
}

const CampaignManagementViewWithContext = () => {
  const appLayoutRef = useRef<AppLayoutProps.Ref>();

  const [toolsOpen, setToolsOpen] = useState(false);
  const [toolsContent, setToolsContent] = useState(() => <CampaignsMainInfo />);

  const loadHelpPanelContent: any = (
    content: SetStateAction<JSX.Element>,
  ): any => {
    setToolsOpen(true);
    setToolsContent(content);
    appLayoutRef.current?.focusToolsClose();
  };

  const cmc = useContext(CampaignManagementContext);

  return (
    <HelpPanelProvider value={loadHelpPanelContent}>
      <AppLayout
        contentType="table"
        breadcrumbs={
          <Breadcrumbs items={cmc.breadcrumbs.breadcrumbItems}></Breadcrumbs>
        }
        navigation={<Navigation activeHref={UI_ROUTES.CAMPAIGN_MANAGEMENT} />}
        toolsOpen={toolsOpen}
        tools={toolsContent}
        onToolsChange={({ detail }) => setToolsOpen(detail.open)}
        content={<Content></Content>}
      />
    </HelpPanelProvider>
  );
};
