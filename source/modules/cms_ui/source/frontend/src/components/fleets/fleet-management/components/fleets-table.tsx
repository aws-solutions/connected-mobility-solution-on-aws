// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Button,
  Pagination,
  Table,
  TextFilter,
  SpaceBetween,
  Link,
  Box,
} from "@cloudscape-design/components";
import { useNavigate } from "react-router-dom";
import ItemState from "../item-state";
import {
  createTableSortLabelFn,
  getHeaderCounterText,
  getTextFilterCounterText,
  renderAriaLive,
} from "@/i18n-strings";
import {
  TableEmptyState,
  TableNoMatchState,
} from "@/components/commons/common-components";
import { fleetTableAriaLabels } from "../i18-strings/table";
import { FullPageHeader } from "../full-page-header";
import { FleetItem } from "@com.cms.fleetmanagement/api-client";
import { UI_ROUTES } from "@/utils/constants";

const rawColumns = [
  {
    id: "name",
    sortingField: "name",
    header: "Fleet Name",
    cell: (item: FleetItem) => (
      <div>
        <Link href={`#${item.id}`}>{item.name}</Link>
      </div>
    ),
    minWidth: 180,
  },
  {
    id: "totalVehicles",
    sortingField: "totalVehicles",
    header: "Total Vehicles",
    cell: (item: FleetItem) => item.numTotalVehicles,
    minWidth: 120,
  },
  {
    id: "connectedVehicles",
    sortingField: "connectedVehicles",
    cell: (item: FleetItem) => item.numConnectedVehicles,
    header: "Connected",
    minWidth: 120,
  },
  {
    id: "activeFleetCampaigns",
    sortingField: "activeFleetCampaigns",
    cell: (item: FleetItem) => item.numActiveCampaigns,
    header: "Active Fleet Campaigns",
    minWidth: 120,
  },
];
const columnDefinitions = rawColumns.map((column) => ({
  ...column,
  ariaLabel: createTableSortLabelFn(column),
}));

export default function FleetsTable({
  fleets,
  selectedItems,
  onSelectionChange,
  onEdit,
  onDelete,
  isLoading,
  error,
}: any) {
  const {
    items,
    actions,
    filteredItemsCount,
    collectionProps,
    filterProps,
    paginationProps,
  } = useCollection(fleets, {
    filtering: {
      empty: <TableEmptyState resourceName="Fleet" />,
      noMatch: (
        <TableNoMatchState onClearFilter={() => actions.setFiltering("")} />
      ),
    },
    pagination: { pageSize: 50 },
    sorting: { defaultState: { sortingColumn: columnDefinitions[0] } },
    selection: {},
  });

  const navigate = useNavigate();

  let emptyTitle: string;
  let emptyMessage: string;

  if (error) {
    emptyTitle = "Error loading fleets";
    if (error.name === "403") {
      emptyMessage = "You do not have permission to view fleets.";
    } else {
      emptyMessage = "An error occurred while loading fleets.";
    }
  } else {
    emptyTitle = "No fleets";
    emptyMessage = "No fleets found.";
  }

  const emptyContent = (
    <Box textAlign="center" color="inherit">
      <b>{emptyTitle}</b>
      <Box padding={{ bottom: "s" }} variant="p" color="inherit">
        {emptyMessage}
      </Box>
      <Button onClick={() => navigate(UI_ROUTES.FLEET_CREATE)}>
        Create fleet
      </Button>
    </Box>
  );

  return (
    <Table
      {...collectionProps}
      loading={isLoading}
      loadingText="Loading fleets"
      enableKeyboardNavigation={true}
      selectedItems={selectedItems}
      onSelectionChange={onSelectionChange}
      columnDefinitions={columnDefinitions}
      items={items}
      selectionType="multi"
      ariaLabels={fleetTableAriaLabels}
      renderAriaLive={renderAriaLive}
      variant="full-page"
      stickyHeader={true}
      empty={emptyContent}
      header={
        <FullPageHeader
          title="Fleets"
          selectedItemsCount={selectedItems.length}
          counter={getHeaderCounterText(fleets, selectedItems)}
          actions={
            <SpaceBetween size="xs" direction="horizontal">
              <Button disabled={selectedItems.length !== 1} onClick={onEdit}>
                Edit
              </Button>
              <Button disabled={selectedItems.length === 0} onClick={onDelete}>
                Delete
              </Button>
              <Button
                variant="primary"
                onClick={() => navigate(UI_ROUTES.FLEET_CREATE)}
              >
                Create fleet
              </Button>
            </SpaceBetween>
          }
        />
      }
      filter={
        <TextFilter
          {...filterProps}
          filteringAriaLabel="Filter fleets"
          filteringPlaceholder="Find fleets"
          filteringClearAriaLabel="Clear"
          countText={getTextFilterCounterText(filteredItemsCount)}
        />
      }
      pagination={<Pagination {...paginationProps} />}
    />
  );
}
