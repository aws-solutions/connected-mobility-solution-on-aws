// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { useRef, useState, SetStateAction } from "react";
import { AppLayoutProps } from "@cloudscape-design/components";
import { HelpPanelProvider } from "../../commons";
import { FleetVehiclesMapInfo } from "./header";
import { Content } from "./content";

export default function FleetVehiclesMapView() {
  const appLayoutRef = useRef<AppLayoutProps.Ref>();

  const [toolsOpen, setToolsOpen] = useState(false);
  const [toolsContent, setToolsContent] = useState(() => (
    <FleetVehiclesMapInfo />
  ));

  const loadHelpPanelContent: any = (
    content: SetStateAction<JSX.Element>,
  ): any => {
    setToolsOpen(true);
    setToolsContent(content);
    appLayoutRef.current?.focusToolsClose();
  };

  return (
    <HelpPanelProvider value={loadHelpPanelContent}>
      <Content></Content>
    </HelpPanelProvider>
  );
}
