// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState, useContext, ReactElement, useEffect } from "react";
import { ApiContext } from "@/api/provider";
import {
  baseTableAriaLabels,
  createTableSortLabelFn,
  getHeaderCounterText,
  getTextFilterCounterText,
} from "@/i18n-strings";
import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Button,
  Form,
  Header,
  SpaceBetween,
  Table,
  Pagination,
  TextFilter,
} from "@cloudscape-design/components";
import {
  TableEmptyState,
  TableNoMatchState,
} from "@/components/commons/common-components";
import { InfoLink } from "../../../commons";
import { AssociateVehiclesInputPanel } from "./input-panel";
import {
  AssociateVehiclesToFleetInput,
  AssociateVehiclesToFleetCommand,
  ListVehiclesCommand,
  VehicleItem,
} from "@com.cms.fleetmanagement/api-client";
import { UI_ROUTES } from "@/utils/constants";
import { Modal, Box } from "@cloudscape-design/components";
import { useNavigate } from "react-router-dom";
import useLocationHash from "../../fleet-management/use-location-hash";
import { VEHICLE_COLUMN_DEFINITIONS } from "../../fleet-management/components/FleetDetailsPage";

interface BaseFormProps {
  content: React.ReactElement;
  onCancelClick: any;
  onSubmitClick: any;
  header: ReactElement;
}

const vehicleSelectionLabels = {
  ...baseTableAriaLabels,
  itemSelectionLabel: (_data: any, row: any) => `select ${row.name}`,
  selectionGroupLabel: "Vehicles selection",
};

export function VehiclesTable({
  fleetId,
  inputData,
  setInputData,
}: {
  fleetId: string;
  inputData: any;
  setInputData: any;
}) {
  const [selectedItems, setSelectedItems] = useState<VehicleItem[]>([]);
  const [fleetVehicles, setFleetVehicles] = useState<VehicleItem[]>([]);
  const [vehiclesLoading, setVehiclesLoading] = useState<boolean>(true);

  const api = useContext(ApiContext);

  const fetchVehicles = async () => {
    const cmd = new ListVehiclesCommand();
    const output = await api.client.send(cmd);
    setFleetVehicles(output.vehicles || []);
  };

  useEffect(() => {
    setVehiclesLoading(true);
    async function getVehicles() {
      await fetchVehicles();
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
      onSelectionChange={(event) => {
        setSelectedItems(event.detail.selectedItems);
        setInputData({
          id: fleetId,
          vehicleNames: event.detail.selectedItems.map((item) => item.name),
        });
      }}
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
        >
          Vehicles
        </Header>
      }
    />
  );
}

export function FormHeader({ loadHelpPanelContent }: any) {
  return (
    <Header
      variant="h1"
      info={
        <InfoLink
          id="form-main-info-link"
          onFollow={() => loadHelpPanelContent(0)}
        />
      }
      description={"Associate existing vehicles with a fleet."}
    >
      Associate Vehicles
    </Header>
  );
}

function FormActions({ onCancelClick, onSubmitClick }: any) {
  return (
    <SpaceBetween direction="horizontal" size="xs">
      <Button variant="link" onClick={onCancelClick}>
        Cancel
      </Button>
      <Button data-testid="create" variant="primary" onClick={onSubmitClick}>
        Associate Vehicles
      </Button>
    </SpaceBetween>
  );
}

function BaseForm({
  content,
  onCancelClick,
  onSubmitClick,
  header,
}: BaseFormProps) {
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (onSubmitClick) {
          onSubmitClick();
        }
      }}
    >
      <Form
        header={header}
        actions={
          <FormActions
            onCancelClick={onCancelClick}
            onSubmitClick={onSubmitClick}
          />
        }
        errorIconAriaLabel="Error"
      >
        {content}
      </Form>
    </form>
  );
}

const defaultData: AssociateVehiclesToFleetInput = {
  id: "",
  vehicleNames: [],
};

export function FormFull({ loadHelpPanelContent, header }: any) {
  const [data, _setData] = useState<AssociateVehiclesToFleetInput>(defaultData);
  const setData = (updateObj = {}) =>
    _setData((prevData) => ({ ...prevData, ...updateObj }));

  const api = useContext(ApiContext);

  const navigate = useNavigate();
  const locationHash = useLocationHash();

  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalConfig, setModalConfig] = useState<{
    title: string;
    message: string;
    type: "success" | "error";
  }>({
    title: "",
    message: "",
    type: "success",
  });

  const showModal = (
    type: "success" | "error",
    title: string,
    message: string,
  ) => {
    setModalConfig({
      type,
      title,
      message,
    });
    setModalVisible(true);
  };

  const handleModalDismiss = () => {
    setModalVisible(false);

    // If it was a successful submission, we might want to perform additional actions
    if (modalConfig.type === "success") {
      navigate(`${UI_ROUTES.FLEET_MANAGEMENT}#${locationHash}`);
    }
  };

  const associateVehiclesToFleet = async () => {
    try {
      const cmd = new AssociateVehiclesToFleetCommand(data);
      const response = await api.client.send(cmd);

      if (response.$metadata.httpStatusCode == 200) {
        showModal(
          "success",
          "Success!",
          "Vehicles associated with the fleet successfully!",
        );
        // Reset form
        setData(defaultData);
      } else {
        showModal(
          "error",
          "Failed",
          "There was an error associating vehicles to the fleet. Please try again.",
        );
      }
    } catch (error) {
      showModal(
        "error",
        "Error",
        "An unexpected error occurred. Please try again later.",
      );
      console.error("Submit error:", error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    await associateVehiclesToFleet();
  };
  return (
    <div>
      <BaseForm
        header={header}
        content={
          <SpaceBetween size="l">
            <AssociateVehiclesInputPanel />
            <VehiclesTable
              fleetId={locationHash}
              inputData={data}
              setInputData={setData}
            />
          </SpaceBetween>
        }
        onCancelClick={() => {
          setData(defaultData);
          navigate(`${UI_ROUTES.FLEET_MANAGEMENT}#${locationHash}`);
        }}
        onSubmitClick={onSubmit}
      />
      <Modal
        visible={modalVisible}
        onDismiss={handleModalDismiss}
        header={modalConfig.title}
        closeAriaLabel="Close modal"
      >
        <Box
          color={
            modalConfig.type === "success"
              ? "text-status-success"
              : "text-status-error"
          }
        >
          <SpaceBetween size="m">
            <Box>{modalConfig.message}</Box>
            <Button onClick={handleModalDismiss} variant="primary">
              {modalConfig.type === "success" ? "Continue" : "Close"}
            </Button>
          </SpaceBetween>
        </Box>
      </Modal>
    </div>
  );
}
