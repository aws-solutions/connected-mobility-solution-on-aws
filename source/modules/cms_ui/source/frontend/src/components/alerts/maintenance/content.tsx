// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useState } from "react";
import {
  Button,
  SpaceBetween,
  Box,
  TextFilter,
  Header,
  Table,
  StatusIndicator,
} from "@cloudscape-design/components";
import { PageBanner } from "@/components/dashboard/components/page-banner";
import { DashboardHeader } from "../header";
import { UserContext } from "@/components/commons/UserContext";
import { FleetSelectionItem } from "@/components/commons/fleet-selection";

interface ContentProps {}

export function Content({}: ContentProps) {
  const [expandedItems, setExpandedItems] = React.useState<Array<any>>([]);

  const [refreshInProgress, setRefreshInProgress] = useState(false);

  function handleRefresh(): void {}

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
            <Button iconName="add-plus" onClick={() => {}}>
              Create Alert
            </Button>
          </SpaceBetween>
        }
      />
      <FleetSelectionItem></FleetSelectionItem>
      <PageBanner />
      <Table
        renderAriaLive={({ firstIndex, lastIndex, totalItemsCount }) =>
          `Displaying items ${firstIndex} to ${lastIndex} of ${totalItemsCount}`
        }
        renderLoaderPending={() => (
          <Button variant="inline-link" iconName="add-plus">
            Show more
          </Button>
        )}
        renderLoaderLoading={() => (
          <StatusIndicator type="loading">Loading items</StatusIndicator>
        )}
        renderLoaderError={() => (
          <StatusIndicator type="error">Loading error</StatusIndicator>
        )}
        expandableRows={{
          getItemChildren: (item) => (item.children ? item.children : []),
          isItemExpandable: (item) => Boolean(item.children),
          expandedItems: expandedItems,
          onExpandableItemToggle: ({ detail }) =>
            setExpandedItems((prev) => {
              const next = new Set((prev ?? []).map((item) => item.name));
              detail.expanded
                ? next.add(detail.item.name)
                : next.delete(detail.item.name);
              return [...next].map((name) => ({ name }));
            }),
        }}
        columnDefinitions={[
          {
            id: "vehicleID",
            header: "Vehicle ID",
            cell: (e) => e.vehicleID,
            isRowHeader: true,
          },
          {
            id: "alertType",
            header: "Alert Type",
            cell: (e) => e.alertType,
          },
          {
            id: "priority",
            header: "Priority",
            cell: (e) => e.priority,
          },
          {
            id: "timestamp",
            header: "Timestamp",
            cell: (e) => e.timestamp,
          },
          {
            id: "status",
            header: "Status",
            cell: (e) => e.status,
          },
          {
            id: "description",
            header: "Description",
            cell: (e) => e.description,
          },
        ]}
        enableKeyboardNavigation
        getLoadingStatus={(item) =>
          !item
            ? "pending"
            : item.name === "Item 5"
              ? "loading"
              : item.name === "Item 6"
                ? "error"
                : "finished"
        }
        items={[
          {
            alertID: "AL-001",
            vehicleID: "VH-1001",
            alertType: "Battery Low",
            priority: "High",
            timestamp: "2024-11-13 10:30 AM",
            status: "Active",
            description: "The battery level is critically low",
            children: [
              {
                alertID: "AL-001-A",
                vehicleID: "VH-1001",
                alertType: "Battery Low",
                priority: "High",
                timestamp: "2024-11-13 10:45 AM",
                status: "Acknowledged",
                description: "Battery level warning acknowledged by technician",
              },
            ],
          },
          {
            alertID: "AL-002",
            vehicleID: "VH-1002",
            alertType: "Tire Pressure",
            priority: "Medium",
            timestamp: "2024-11-13 11:00 AM",
            status: "Resolved",
            description: "The tire pressure is below the recommended level",
          },
          {
            alertID: "AL-003",
            vehicleID: "VH-1003",
            alertType: "Engine Overheat",
            priority: "Critical",
            timestamp: "2024-11-13 11:30 AM",
            status: "Active",
            description: "The engine temperature is critically high",
          },
        ]}
        loadingText="Loading resources"
        trackBy="name"
        empty={
          <Box margin={{ vertical: "xs" }} textAlign="center" color="inherit">
            <SpaceBetween size="m">
              <b>No resources</b>
              <Button>Create resource</Button>
            </SpaceBetween>
          </Box>
        }
        filter={
          <TextFilter filteringPlaceholder="Find resources" filteringText="" />
        }
        header={<Header>Maintenance Alerts</Header>}
      />
    </SpaceBetween>
  );
}
