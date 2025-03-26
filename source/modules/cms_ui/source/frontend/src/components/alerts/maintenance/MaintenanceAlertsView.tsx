// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState, SetStateAction } from "react";
import { AppLayoutProps, AppLayout } from "@cloudscape-design/components";
import { HelpPanelProvider } from "../../commons";
import { Navigation } from "../../commons/common-components";
import { AlertsMainInfo } from "../header";
import { Content } from "./content";
import { UI_ROUTES } from "@/utils/constants";
import { AlertsBreadcrumbs } from "../breadcrumbs";

export default function MaintenanceAlertsView() {
  const appLayoutRef = useRef<AppLayoutProps.Ref>();

  const [toolsOpen, setToolsOpen] = useState(false);
  const [toolsContent, setToolsContent] = useState(() => <AlertsMainInfo />);

  const loadHelpPanelContent: any = (
    content: SetStateAction<JSX.Element>,
  ): any => {
    setToolsOpen(true);
    setToolsContent(content);
    appLayoutRef.current?.focusToolsClose();
  };

  // const appLayout = useRef();

  return (
    <HelpPanelProvider value={loadHelpPanelContent}>
      <AppLayout
        // ref={appLayoutRef}
        contentType="dashboard"
        breadcrumbs={
          <AlertsBreadcrumbs
            items={[
              {
                text: "Maintenance Alerts",
                href: UI_ROUTES.ALERTS_MAINTENANCE,
              },
            ]}
          />
        }
        navigation={<Navigation activeHref={UI_ROUTES.ALERTS_MAINTENANCE} />}
        toolsOpen={toolsOpen}
        tools={toolsContent}
        // onToolsChange={({ detail }) => setToolsOpen(detail.open)}
        content={<Content></Content>}
      />
    </HelpPanelProvider>
  );
}
