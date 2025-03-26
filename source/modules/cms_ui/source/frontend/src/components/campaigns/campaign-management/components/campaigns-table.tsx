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
  StatusIndicator,
  Box,
} from "@cloudscape-design/components";
import { useNavigate } from "react-router-dom";
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
import { campaignTableAriaLabels } from "../i18-strings/table";
import { FullPageHeader } from "../full-page-header";
import {
  CampaignItem,
  CampaignStatus,
} from "@com.cms.fleetmanagement/api-client";
import { UI_ROUTES } from "@/utils/constants";

const rawColumns = [
  {
    id: "name",
    sortingField: "name",
    header: "Campaign Name",
    cell: (item: CampaignItem) => (
      <div>
        <Link href={`#${item.name}`}>{item.name}</Link>
      </div>
    ),
    minWidth: 180,
  },
  {
    id: "status",
    sortingField: "status",
    cell: (item: CampaignItem) => {
      switch (item.status) {
        case CampaignStatus.RUNNING:
          return (
            <StatusIndicator type={"success"}>{item.status}</StatusIndicator>
          );
        case CampaignStatus.CREATING:
          return (
            <StatusIndicator type={"in-progress"}>
              {item.status}
            </StatusIndicator>
          );
        case CampaignStatus.SUSPENDED:
          return (
            <StatusIndicator type={"warning"}>{item.status}</StatusIndicator>
          );
        case CampaignStatus.WAITING_FOR_APPROVAL:
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
];
const columnDefinitions = rawColumns.map((column) => ({
  ...column,
  ariaLabel: createTableSortLabelFn(column),
}));

export default function CampaignsTable({
  campaigns,
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
  } = useCollection(campaigns, {
    filtering: {
      empty: <TableEmptyState resourceName="Campaign" />,
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
    emptyTitle = "Error loading campaigns";
    if (error.name === "403") {
      emptyMessage = "You do not have permission to view campaigns.";
    } else {
      emptyMessage = "An error occurred while loading campaigns.";
    }
  } else {
    emptyTitle = "No campaigns";
    emptyMessage = "No campaigns found.";
  }

  const emptyContent = (
    <Box textAlign="center" color="inherit">
      <b>{emptyTitle}</b>
      <Box padding={{ bottom: "s" }} variant="p" color="inherit">
        {emptyMessage}
      </Box>
      {/* <Button onClick={() => navigate(UI_ROUTES.CAMPAIGN_CREATE)}>
        Create campaign
      </Button> */}
    </Box>
  );

  return (
    <Table
      {...collectionProps}
      loading={isLoading}
      loadingText="Loading campaigns"
      enableKeyboardNavigation={true}
      selectedItems={selectedItems}
      onSelectionChange={onSelectionChange}
      columnDefinitions={columnDefinitions}
      items={items}
      selectionType="multi"
      ariaLabels={campaignTableAriaLabels}
      renderAriaLive={renderAriaLive}
      variant="full-page"
      stickyHeader={true}
      empty={emptyContent}
      header={
        <FullPageHeader
          title="Campaigns"
          selectedItemsCount={selectedItems.length}
          counter={getHeaderCounterText(campaigns, selectedItems)}
          actions={
            <SpaceBetween size="xs" direction="horizontal">
              <Button disabled={true} onClick={onDelete}>
                Delete
              </Button>
              <Button
                disabled={true}
                variant="primary"
                onClick={() => navigate(UI_ROUTES.CAMPAIGN_CREATE)}
              >
                Create campaign
              </Button>
            </SpaceBetween>
          }
        />
      }
      filter={
        <TextFilter
          {...filterProps}
          filteringAriaLabel="Filter campaigns"
          filteringPlaceholder="Find campaigns"
          filteringClearAriaLabel="Clear"
          countText={getTextFilterCounterText(filteredItemsCount)}
        />
      }
      pagination={<Pagination {...paginationProps} />}
    />
  );
}
