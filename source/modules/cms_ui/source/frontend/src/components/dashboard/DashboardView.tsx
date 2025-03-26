// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState } from "react";
import {
  AppLayout,
  SplitPanel,
  AppLayoutProps,
} from "@cloudscape-design/components";
import { HelpPanelProvider } from "../commons";
import { Navigation } from "../commons/common-components";
import { useLocalStorage } from "../commons/use-local-storage";
import { UI_ROUTES } from "../../utils/constants";
import { DashboardMainInfo } from "./header";
import { Content } from "./content";
import Palette from "./components/palette";
import { getPaletteWidgets } from "./widgets";
import { Breadcrumbs } from "../commons/breadcrumbs";
import { StoredWidgetPlacement } from "./interfaces";

const splitPanelMaxSize = 360;

export default function DashboardView() {
  const appLayoutRef = useRef<AppLayoutProps.Ref>();

  const [toolsOpen, setToolsOpen] = useState(false);
  const [splitPanelOpen, setSplitPanelOpen] = useState(false);
  const [splitPanelSize, setSplitPanelSize] = useLocalStorage(
    "React-ConfigurableDashboard-SplitPanelSize",
    360,
  );
  const [layout, setLayout, resetLayout] =
    useLocalStorage<ReadonlyArray<StoredWidgetPlacement> | null>(
      "FleetsDashboard-widgets-layout",
      null,
    );
  const [toolsContent, setToolsContent] = useState(() => <DashboardMainInfo />);

  const loadHelpPanelContent: any = (
    content: React.SetStateAction<JSX.Element>,
  ) => {
    setToolsOpen(true);
    setToolsContent(content);
    appLayoutRef.current?.focusToolsClose();
  };

  return (
    <HelpPanelProvider value={loadHelpPanelContent}>
      <AppLayout
        // ref={appLayoutRef}
        contentType="dashboard"
        breadcrumbs={
          <Breadcrumbs items={[{ text: "Dashboard", href: UI_ROUTES.ROOT }]} />
        }
        navigation={<Navigation activeHref={UI_ROUTES.ROOT} />}
        toolsOpen={toolsOpen}
        tools={toolsContent}
        onToolsChange={({ detail }) => setToolsOpen(detail.open)}
        content={
          <Content
            layout={layout}
            setLayout={setLayout}
            resetLayout={resetLayout}
            setSplitPanelOpen={setSplitPanelOpen}
          />
        }
        splitPanel={
          <SplitPanel
            header="Add widgets"
            closeBehavior="hide"
            hidePreferencesButton={true}
          >
            <Palette items={getPaletteWidgets(layout ?? [])} />
          </SplitPanel>
        }
        splitPanelPreferences={{ position: "side" }}
        splitPanelOpen={splitPanelOpen}
        onSplitPanelToggle={({ detail }) => setSplitPanelOpen(detail.open)}
        splitPanelSize={splitPanelSize}
        onSplitPanelResize={(event) =>
          setSplitPanelSize(Math.min(event.detail.size, splitPanelMaxSize))
        }
      />
    </HelpPanelProvider>
  );
}
