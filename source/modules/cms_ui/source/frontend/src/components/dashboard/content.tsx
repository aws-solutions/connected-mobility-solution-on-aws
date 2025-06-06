// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { DashboardHeader } from "./header";
import { ResetButton } from "./components/reset-button";
import { PageBanner } from "./components/page-banner";
import Board from "@cloudscape-design/board-components/board";
import { EmptyState } from "./components/empty-state";
import { boardI18nStrings } from "../../i18n-strings";
import { exportLayout, getBoardWidgets, getDefaultLayout } from "./widgets";
import React, { useContext, useEffect, useRef, useState } from "react";
import { useContainerQuery } from "@cloudscape-design/component-toolkit";
import { ConfigurableWidget } from "./components/configurable-widget";
import { StoredWidgetPlacement } from "./interfaces";
import { Button, SpaceBetween, Box } from "@cloudscape-design/components";
import { UserContext } from "../commons/UserContext";
import { FleetSelectionItem } from "../commons/fleet-selection";
import { UI_ROUTES } from "@/utils/constants";
import { useNavigate } from "react-router-dom";

interface ContentProps {
  layout: ReadonlyArray<StoredWidgetPlacement> | null;
  setLayout: (newLayout: ReadonlyArray<StoredWidgetPlacement>) => void;
  resetLayout: (newLayout: ReadonlyArray<StoredWidgetPlacement>) => void;
  setSplitPanelOpen: (newOpen: boolean) => void;
}

type SelectContent = {
  label: string;
  value: string;
};

export function Content({
  layout,
  setLayout,
  resetLayout,
  setSplitPanelOpen,
}: ContentProps) {
  const [width, ref] = useContainerQuery((entry) => entry.contentBoxWidth);
  const itemsChanged = useRef(layout !== null);

  const uc = useContext(UserContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (itemsChanged.current || !width) {
      return;
    }
    resetLayout(getDefaultLayout(width));
  }, [resetLayout, width]);

  function handleLayoutChange(layout: ReadonlyArray<StoredWidgetPlacement>) {
    itemsChanged.current = true;
    setLayout(layout);
  }

  function handleResetLayout() {
    itemsChanged.current = false;
    resetLayout(getDefaultLayout(width!));
  }

  const [refreshInProgress, setRefreshInProgress] = useState(false);

  const handleRefresh = async () => {
    if (refreshInProgress) return; // Prevent further refreshes until current is done

    setRefreshInProgress(true);

    setRefreshInProgress(false); // Allow future refreshes
  };

  return (
    <SpaceBetween size="m">
      <DashboardHeader
        actions={
          <SpaceBetween size="xs" direction="horizontal">
            <Button
              iconName="refresh"
              onClick={() => handleRefresh()}
              disabled={refreshInProgress}
              disabledReason="Refresh in progress..."
            >
              Refresh
            </Button>
            <ResetButton onReset={handleResetLayout}>
              Reset to default layout
            </ResetButton>
            <Button iconName="add-plus" onClick={() => setSplitPanelOpen(true)}>
              Add widget
            </Button>
          </SpaceBetween>
        }
      />
      <FleetSelectionItem></FleetSelectionItem>
      <PageBanner />
      <div ref={ref}>
        {uc.fleet.selectedFleet ? (
          <Board
            empty={
              <EmptyState
                title="No widgets"
                description="There are no widgets on the dashboard."
                verticalCenter={true}
                action={
                  <SpaceBetween direction="horizontal" size="xs">
                    <Button onClick={handleResetLayout}>
                      Reset to default layout
                    </Button>
                    <Button
                      iconName="add-plus"
                      onClick={() => setSplitPanelOpen(true)}
                    >
                      Add widget
                    </Button>
                  </SpaceBetween>
                }
              />
            }
            i18nStrings={boardI18nStrings}
            items={getBoardWidgets(layout ?? [])}
            onItemsChange={({ detail: { items } }) => {
              handleLayoutChange(exportLayout(items));
            }}
            renderItem={(item, actions) => {
              console.log("hit");
              const Wrapper = item.data.provider ?? React.Fragment;
              return (
                <Wrapper>
                  <ConfigurableWidget
                    config={item.data}
                    onRemove={actions.removeItem}
                  />
                </Wrapper>
              );
            }}
          />
        ) : (
          <div>
            <Box textAlign="center" color="inherit">
              <b>No fleet selected</b>
              <Box padding={{ bottom: "s" }} variant="p" color="inherit">
                Select a fleet from the dropdown to populate the dashboard.
              </Box>
            </Box>
          </div>
        )}
      </div>
    </SpaceBetween>
  );
}
