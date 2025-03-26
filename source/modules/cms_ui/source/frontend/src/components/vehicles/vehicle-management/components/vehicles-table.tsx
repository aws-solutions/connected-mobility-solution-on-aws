// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Button,
  Pagination,
  Box,
  Table,
  TextFilter,
  SpaceBetween,
  Link,
} from "@cloudscape-design/components";
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
import { vehicleTableAriaLabels } from "../i18-strings/table";
import { FullPageHeader } from "../full-page-header";
import {
  VehicleItem,
  VehicleStatus,
} from "@com.cms.fleetmanagement/api-client";
import { StatusIndicator } from "@cloudscape-design/components";
import { UI_ROUTES } from "@/utils/constants";
import { useNavigate } from "react-router-dom";

const rawColumns = [
  {
    id: "name",
    sortingField: "name",
    header: "Vehicle Name",
    cell: (item: VehicleItem) => (
      <div>
        <Link href={`#${item.name}`}>{item.name}</Link>
      </div>
    ),
    minWidth: 100,
  },
  {
    id: "status",
    sortingField: "status",
    cell: (item: VehicleItem) => {
      switch (item.status) {
        case VehicleStatus.ACTIVE:
          return (
            <StatusIndicator type={"success"}>{item.status}</StatusIndicator>
          );
        case VehicleStatus.INACTIVE:
          return (
            <StatusIndicator type={"in-progress"}>
              {item.status}
            </StatusIndicator>
          );
        default:
          return (
            <StatusIndicator type={"warning"}>{"unknown"}</StatusIndicator>
          );
      }
    },
    header: "Status",
    minWidth: 120,
  },
  {
    id: "make",
    sortingField: "make",
    header: "Make",
    cell: (item: VehicleItem) => item.attributes.make,
    minWidth: 70,
  },
  {
    id: "model",
    sortingField: "model",
    header: "Model",
    cell: (item: VehicleItem) => item.attributes.model,
    minWidth: 70,
  },
  {
    id: "year",
    sortingField: "year",
    header: "Year",
    cell: (item: VehicleItem) => item.attributes.year,
    minWidth: 70,
  },
  {
    id: "licensePlate",
    sortingField: "licensePlate",
    header: "License Plate",
    cell: (item: VehicleItem) => item.attributes.licensePlate,
    minWidth: 70,
  },
];
const columnDefinitions = rawColumns.map((column) => ({
  ...column,
  ariaLabel: createTableSortLabelFn(column),
}));

export default function VehiclesTable({
  vehicles,
  selectedItems,
  onSelectionChange,
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
  } = useCollection(vehicles, {
    filtering: {
      empty: <TableEmptyState resourceName="Vehicle" />,
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
    emptyTitle = "Error loading vehicles";
    if (error.name === "403") {
      emptyMessage = "You do not have permission to view vehicles.";
    } else {
      emptyMessage = "An error occurred while loading vehicles.";
    }
  } else {
    emptyTitle = "No vehicles";
    emptyMessage = "No vehicles found.";
  }

  const emptyContent = (
    <Box textAlign="center" color="inherit">
      <b>{emptyTitle}</b>
      <Box padding={{ bottom: "s" }} variant="p" color="inherit">
        {emptyMessage}
      </Box>
      <Button onClick={() => navigate(UI_ROUTES.VEHICLE_CREATE)}>
        Create vehicle
      </Button>
    </Box>
  );

  return (
    <Table
      {...collectionProps}
      loading={isLoading}
      loadingText="Loading vehicles"
      enableKeyboardNavigation={true}
      selectedItems={selectedItems}
      onSelectionChange={onSelectionChange}
      columnDefinitions={columnDefinitions}
      items={items}
      selectionType="multi"
      ariaLabels={vehicleTableAriaLabels}
      renderAriaLive={renderAriaLive}
      variant="full-page"
      stickyHeader={true}
      empty={emptyContent}
      header={
        <FullPageHeader
          title="Vehicles"
          selectedItemsCount={selectedItems.length}
          counter={getHeaderCounterText(vehicles, selectedItems)}
          actions={
            <SpaceBetween size="xs" direction="horizontal">
              <Button
                disabled={selectedItems.length !== 1}
                onClick={() =>
                  navigate(`${UI_ROUTES.VEHICLE_EDIT}#${selectedItems[0].name}`)
                }
              >
                Edit
              </Button>
              <Button disabled={selectedItems.length === 0} onClick={onDelete}>
                Delete
              </Button>
              <Button
                variant="primary"
                onClick={() => navigate(UI_ROUTES.VEHICLE_CREATE)}
              >
                Create vehicle
              </Button>
            </SpaceBetween>
          }
        />
      }
      filter={
        <TextFilter
          {...filterProps}
          filteringAriaLabel="Filter vehicles"
          filteringPlaceholder="Find vehicles"
          filteringClearAriaLabel="Clear"
          countText={getTextFilterCounterText(filteredItemsCount)}
        />
      }
      pagination={<Pagination {...paginationProps} />}
    />
  );
}
