// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState } from "react";
import {
  AppLayout,
  SplitPanel,
  AppLayoutProps,
} from "@cloudscape-design/components";
import { useLocalStorage } from "@/components/commons/use-local-storage";
import { Content } from "./content";
import Palette from "./components/palette";
import { getPaletteWidgets } from "./widgets";
import { StoredWidgetPlacement } from "./interfaces";

const splitPanelMaxSize = 360;

export default function VehicleDashboardView({ vehicle, notifications }: any) {
  const appLayoutRef = useRef<AppLayoutProps.Ref>();

  const [splitPanelOpen, setSplitPanelOpen] = useState(false);
  const [splitPanelSize, setSplitPanelSize] = useLocalStorage(
    "React-ConfigurableDashboard-SplitPanelSize",
    360,
  );
  const [layout, setLayout, resetLayout] =
    useLocalStorage<ReadonlyArray<StoredWidgetPlacement> | null>(
      "VehicleDashboard-widgets-layout",
      null,
    );

  const appLayout = useRef();

  return (
    <AppLayout
      contentType="dashboard"
      toolsHide={true}
      navigationHide={true}
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
  );
}
