// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  TableEmptyState,
  TableNoMatchState,
} from "@/components/commons/common-components";
import {
  baseTableAriaLabels,
  createTableSortLabelFn,
  getHeaderCounterText,
  getTextFilterCounterText,
} from "@/i18n-strings";
import {
  AppLayout,
  Box,
  Button,
  Container,
  Flashbar,
  Header,
  KeyValuePairs,
  SpaceBetween,
  StatusIndicator,
  Table,
  Pagination,
  TextFilter,
} from "@cloudscape-design/components";
import { ReactNode, useEffect, useState, useContext } from "react";
import { ApiContext } from "@/api/provider";
import {
  FleetItem,
  GetFleetCommand,
  CampaignItem,
  CampaignStatus,
  ListCampaignsForTargetCommand,
  ListVehiclesInFleetCommand,
  VehicleItem,
  VehicleStatus,
  CampaignTargetType,
  StartCampaignCommand,
  StopCampaignCommand,
  DeleteCampaignCommand,
  DisassociateVehicleCommand,
} from "@com.cms.fleetmanagement/api-client";
import { useCollection } from "@cloudscape-design/collection-hooks";
import { useNavigate } from "react-router-dom";
import { UI_ROUTES } from "@/utils/constants";

export function FleetDetailsPage({
  fleetId,
  onDeleteInit,
  notifications,
}: any) {
  const [fleet, setFleet] = useState<FleetItem>();
  const [fleetCampaigns, setFleetCampaigns] = useState<CampaignItem[]>([]);
  const [campaignsLoading, setCampaignsLoading] = useState<boolean>(true);

  const api = useContext(ApiContext);

  const fetchFleet = async (fleetId: string) => {
    const input = { id: fleetId };
    const cmd = new GetFleetCommand(input);
    const output = await api.client.send(cmd);
    setFleet(output);
  };

  useEffect(() => {
    async function getFleet() {
      await fetchFleet(fleetId);
    }
    getFleet();
  }, [window.location.hash]);

  const fetchFleetCampaigns = async (fleetId: string) => {
    const input = { targetId: fleetId, targetType: CampaignTargetType.FLEET };
    const cmd = new ListCampaignsForTargetCommand(input);
    const output = await api.client.send(cmd);
    setFleetCampaigns(output.campaigns || []);
  };

  useEffect(() => {
    setCampaignsLoading(true);
    async function getCampaigns() {
      await fetchFleetCampaigns(fleetId);
    }
    getCampaigns();
    setCampaignsLoading(false);
  }, []);

  return (
    <AppLayout
      content={
        <SpaceBetween size="m">
          <Header
            variant="h1"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button>Edit</Button>
                <Button onClick={onDeleteInit}>Delete</Button>
              </SpaceBetween>
            }
          >
            {fleet?.name}
          </Header>
          <SpaceBetween size="l">
            <Container header={<Header variant="h2">Fleet details</Header>}>
              <FleetDetails fleet={fleet} />
            </Container>
            <FleetCampaignsTable
              fleetId={fleetId}
              fleetCampaigns={fleetCampaigns}
              setFleetCampaigns={setFleetCampaigns}
              campaignsLoading={campaignsLoading}
            />
            {fleet?.id && <FleetVehiclesTable fleetId={fleet?.id} />}
          </SpaceBetween>
        </SpaceBetween>
      }
      notifications={<Flashbar items={notifications} stackItems={true} />}
      navigationOpen={false}
      navigationHide={true}
      toolsHide={true}
    />
  );
}

export function FleetDetails({
  fleet,
}: {
  fleet: FleetItem | undefined;
}): ReactNode {
  if (!fleet) {
    return;
  }
  return (
    <KeyValuePairs
      columns={4}
      items={[
        {
          type: "group",
          items: [
            {
              label: "Fleet Name",
              value: fleet.name,
            },
            {
              label: "Fleet ID",
              value: fleet.id,
            },
          ],
        },
        {
          type: "group",
          items: [
            {
              label: "Total Vehicles",
              value: fleet.numTotalVehicles,
            },
            {
              label: "Connected Vehicles",
              value: fleet.numConnectedVehicles,
            },
          ],
        },
        {
          type: "group",
          items: [
            {
              label: "Total Campaigns",
              value: fleet.numTotalCampaigns,
            },
            {
              label: "Active Fleet Campaigns",
              value: fleet.numActiveCampaigns,
            },
          ],
        },
        {
          type: "group",
          items: [
            {
              label: "Created",
              value: fleet.createdTime,
            },
            {
              label: "Last Modified",
              value: fleet.lastModifiedTime,
            },
          ],
        },
      ]}
    />
  );
}

const CAMPAIGN_COLUMN_DEFINITIONS = [
  {
    id: "name",
    header: "Name",
    cell: (item: FleetItem) => item.name,
    isRowHeader: true,
  },
  {
    id: "status",
    header: "Status",
    cell: (item: CampaignItem) => {
      const getStatusIndicator = (status: CampaignStatus | undefined) => {
        if (status === CampaignStatus.RUNNING) {
          return (
            <StatusIndicator type="success">
              {CampaignStatus.RUNNING}
            </StatusIndicator>
          );
        } else if (status === CampaignStatus.SUSPENDED) {
          return (
            <StatusIndicator type="stopped">
              {CampaignStatus.SUSPENDED}
            </StatusIndicator>
          );
        } else if (status === CampaignStatus.CREATING) {
          return (
            <StatusIndicator type="in-progress">
              {CampaignStatus.CREATING}
            </StatusIndicator>
          );
        } else if (status === CampaignStatus.WAITING_FOR_APPROVAL) {
          return (
            <StatusIndicator type="in-progress">
              {CampaignStatus.WAITING_FOR_APPROVAL}
            </StatusIndicator>
          );
        }
      };

      return getStatusIndicator(item.status);
    },
    minWidth: 200,
  },
];

export const VEHICLE_COLUMN_DEFINITIONS = [
  {
    id: "vehicleName",
    sortingField: "vehicleName",
    header: "Name",
    cell: (item: VehicleItem) => item.name,
    isRowHeader: true,
  },
  {
    id: "status",
    sortingField: "status",
    header: "Status",
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
  },
  {
    id: "make",
    sortingField: "make",
    header: "Make",
    cell: (item: VehicleItem) => item.attributes?.make,
    isRowHeader: true,
  },
  {
    id: "model",
    sortingField: "model",
    header: "Model",
    cell: (item: VehicleItem) => item.attributes?.model,
    isRowHeader: true,
  },
  {
    id: "year",
    sortingField: "year",
    header: "Year",
    cell: (item: VehicleItem) => item.attributes?.year,
    isRowHeader: true,
  },
  {
    id: "licensePlate",
    sortingField: "licensePlate",
    header: "License Plate",
    cell: (item: VehicleItem) => item.attributes?.licensePlate,
    isRowHeader: true,
  },
];

const campaignsSelectionLabels = {
  ...baseTableAriaLabels,
  itemSelectionLabel: (_data: any, row: any) => `select ${row.name}`,
  selectionGroupLabel: "Campaigns selection",
};

const vehicleSelectionLabels = {
  ...baseTableAriaLabels,
  itemSelectionLabel: (_data: any, row: any) => `select ${row.name}`,
  selectionGroupLabel: "Vehicles selection",
};

export function FleetCampaignsTable({
  fleetId,
  fleetCampaigns,
  setFleetCampaigns,
  campaignsLoading,
}: {
  fleetId: string;
  fleetCampaigns: CampaignItem[];
  setFleetCampaigns: any;
  campaignsLoading: boolean;
}) {
  const [selectedItems, setSelectedItems] = useState<any>([]);
  const enableStopCampaignButton =
    selectedItems.length > 0 && selectedItems[0].status === "RUNNING";
  const enableStartCampaignButton =
    selectedItems.length > 0 && selectedItems[0].status !== "RUNNING";
  const atLeastOneSelected = selectedItems.length > 0;

  const api = useContext(ApiContext);

  const onStartCampaign = async () => {
    const input = { name: selectedItems[0].name };
    const cmd = new StartCampaignCommand(input);
    await api.client.send(cmd);
    setSelectedItems([]);
  };

  const onStopCampaign = async () => {
    const input = { name: selectedItems[0].name };
    const cmd = new StopCampaignCommand(input);
    await api.client.send(cmd);
    setSelectedItems([]);
  };

  const onDeleteCampaign = async () => {
    const input = { name: selectedItems[0].name };
    const cmd = new DeleteCampaignCommand(input);
    await api.client.send(cmd);
    setSelectedItems([]);

    const getCampaignsCommand = new ListCampaignsForTargetCommand({
      targetId: fleetId,
      targetType: CampaignTargetType.FLEET,
    });
    const campaignsOutput = await api.client.send(getCampaignsCommand);
    setFleetCampaigns(campaignsOutput.campaigns || []);
  };

  return (
    <Table
      enableKeyboardNavigation={true}
      columnDefinitions={CAMPAIGN_COLUMN_DEFINITIONS}
      loading={campaignsLoading}
      loadingText="Loading campaigns"
      items={fleetCampaigns}
      ariaLabels={campaignsSelectionLabels}
      selectionType="single"
      selectedItems={selectedItems}
      onSelectionChange={(event) =>
        setSelectedItems(event.detail.selectedItems)
      }
      header={
        <Header
          counter={
            !campaignsLoading && fleetCampaigns
              ? getHeaderCounterText(fleetCampaigns, selectedItems)
              : undefined
          }
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button disabled={!atLeastOneSelected} onClick={onDeleteCampaign}>
                Delete
              </Button>
              <Button
                disabled={!enableStopCampaignButton}
                onClick={onStopCampaign}
              >
                Stop
              </Button>
              <Button
                disabled={!enableStartCampaignButton}
                onClick={onStartCampaign}
              >
                Start
              </Button>
            </SpaceBetween>
          }
        >
          Fleet Campaigns
        </Header>
      }
    />
  );
}
//
export function FleetVehiclesTable({ fleetId }: { fleetId: string }) {
  const [selectedItems, setSelectedItems] = useState<VehicleItem[]>([]);
  const [fleetVehicles, setFleetVehicles] = useState<VehicleItem[]>([]);
  const [vehiclesLoading, setVehiclesLoading] = useState<boolean>(true);
  const atLeastOneSelected = selectedItems.length > 0;

  const api = useContext(ApiContext);
  const navigate = useNavigate();

  const fetchFleetVehicles = async (fleetId: string) => {
    const input = { id: fleetId };
    const cmd = new ListVehiclesInFleetCommand(input);
    const output = await api.client.send(cmd);
    setFleetVehicles(output.vehicles || []);
  };

  const onDisassociateVehicles = async () => {
    selectedItems.map(async (vehicle) => {
      const input = { name: vehicle.name, fleetId: fleetId };
      const cmd = new DisassociateVehicleCommand(input);
      await api.client.send(cmd);
    });
    setSelectedItems([]);
    setVehiclesLoading(true);
    await fetchFleetVehicles(fleetId);
    setVehiclesLoading(false);
  };

  const onAssociateVehicles = async () => {
    navigate(`${UI_ROUTES.FLEET_ASSOCIATE_VEHICLES}#${fleetId}`);
  };

  useEffect(() => {
    setVehiclesLoading(true);
    async function getVehicles() {
      await fetchFleetVehicles(fleetId);
    }
    getVehicles();
    setVehiclesLoading(false);
  }, [fleetId]);

  const columnDefinitions = VEHICLE_COLUMN_DEFINITIONS.map((column) => ({
    ...column,
    ariaLabel: createTableSortLabelFn(column),
  }));

  const {
    items,
    actions,
    filteredItemsCount,
    collectionProps,
    filterProps,
    paginationProps,
  } = useCollection(fleetVehicles, {
    filtering: {
      empty: <TableEmptyState resourceName="Vehicle" />,
      noMatch: (
        <TableNoMatchState onClearFilter={() => actions.setFiltering("")} />
      ),
    },
    pagination: { pageSize: 10 },
    sorting: { defaultState: { sortingColumn: columnDefinitions[0] } },
    selection: {},
  });

  return (
    <Table
      {...collectionProps}
      enableKeyboardNavigation={true}
      columnDefinitions={columnDefinitions}
      loading={vehiclesLoading}
      loadingText="Loading vehicles"
      items={items}
      ariaLabels={vehicleSelectionLabels}
      selectionType="multi"
      selectedItems={selectedItems}
      onSelectionChange={(event) =>
        setSelectedItems(event.detail.selectedItems)
      }
      pagination={<Pagination {...paginationProps} />}
      filter={
        <TextFilter
          {...filterProps}
          filteringAriaLabel="Filter vehicles"
          filteringPlaceholder="Find vehicles"
          filteringClearAriaLabel="Clear"
          countText={getTextFilterCounterText(filteredItemsCount)}
        />
      }
      empty={
        <Box textAlign="center" color="inherit">
          <b>No vehicles</b>
          <Box padding={{ bottom: "s" }} variant="p" color="inherit">
            No vehicles found.
          </Box>
        </Box>
      }
      header={
        <Header
          counter={
            !vehiclesLoading && fleetVehicles
              ? getHeaderCounterText(fleetVehicles, selectedItems)
              : undefined
          }
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                disabled={!atLeastOneSelected}
                onClick={onDisassociateVehicles}
              >
                Disassociate Vehicles
              </Button>
              <Button onClick={onAssociateVehicles}>Associate Vehicles</Button>
            </SpaceBetween>
          }
        >
          Fleet Vehicles
        </Header>
      }
    />
  );
}
