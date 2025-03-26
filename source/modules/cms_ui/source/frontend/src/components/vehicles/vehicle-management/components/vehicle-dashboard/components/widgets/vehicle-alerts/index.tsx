// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import {
  Box,
  Header,
  Link,
  StatusIndicator,
  StatusIndicatorProps,
  Table,
  TableProps,
  Button,
} from "@cloudscape-design/components";
import { WidgetConfig } from "../interfaces";
import { AlertViewType, fetchVehicleAlerts, AlertModalData } from "./data";
import { useNavigate } from "react-router-dom";
import { UI_ROUTES } from "@/utils/constants";
import { VehicleItem } from "@com.cms.fleetmanagement/api-client";
import { VehicleManagementContext } from "@/components/vehicles/vehicle-management/VehicleManagementContext";
import { EmptyState } from "../../empty-state";
import { DynamicModal } from "@/components/commons/dynamic-modal";

export const vehicleAlerts: WidgetConfig = {
  definition: { defaultRowSpan: 3, defaultColumnSpan: 4 },
  data: {
    icon: "table",
    title: "Vehicle Alerts",
    description: "View current vehicle alerts",
    disableContentPaddings: false,
    header: WidgetHeader,
    content: WidgetContent,
    footer: WidgetFooter,
  },
};

function WidgetHeader() {
  return <Header>Vehicle Alerts</Header>;
}

function WidgetFooter() {
  const navigate = useNavigate();

  return (
    <Box textAlign="center">
      <Link
        onClick={() => navigate(UI_ROUTES.ALERTS_MAINTENANCE)}
        variant="primary"
      >
        View all vehicle alerts
      </Link>
    </Box>
  );
}

const alertsDefinition = (
  alertViewOnClickHandler: any,
): Array<TableProps.ColumnDefinition<any>> => [
  {
    id: "name",
    header: "Alert Name",
    cell: (item) => item.name,
    minWidth: 135,
    width: 140,
    isRowHeader: true,
  },
  {
    id: "campaign",
    header: "Campaign",
    cell: (item) => item.campaign,
    minWidth: 135,
    width: 160,
    isRowHeader: true,
  },
  {
    id: "severity",
    header: "Severity",
    cell: ({ severityText, severity }) => (
      <StatusIndicator type={severity as StatusIndicatorProps.Type}>
        {severityText}
      </StatusIndicator>
    ),
    minWidth: 120,
    width: 120,
    maxWidth: 130,
  },
  {
    id: "status",
    header: "Status",
    cell: ({ statusText, status }) => (
      <StatusIndicator type={status as StatusIndicatorProps.Type}>
        {statusText}
      </StatusIndicator>
    ),
    minWidth: 150,
    width: 150,
  },
  {
    id: "view",
    header: "View",
    cell: (item: any) => (
      <Button
        iconName={
          item.viewType == AlertViewType.TEXT
            ? "file"
            : item.viewType == AlertViewType.VIDEO
              ? "video-camera-on"
              : "full-screen"
        }
        variant="icon"
        onClick={() =>
          alertViewOnClickHandler({
            type: item.viewType,
            data: item.viewData,
            title: item.name,
          })
        }
      />
    ),
    minWidth: 80,
    width: 80,
  },
  {
    id: "description",
    header: "Description",
    cell: (item) => item.description,
    hasDynamicContent: true,
    minWidth: 150,
    width: 350,
  },
  {
    id: "timestamp",
    header: "Last Trigger Time",
    cell: (item) => item.timestamp.toLocaleString(),
    minWidth: 100,
    width: 135,
  },
];

let isSubscribed = true;
async function update(
  locationVehicle: VehicleItem | undefined,
  setData: React.Dispatch<React.SetStateAction<any[] | undefined>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (locationVehicle) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const alerts = await fetchVehicleAlerts();
      if (isSubscribed) setData(alerts);
      setDataStatus("finished");
    } catch (e) {
      setDataStatus("error");
    }
  } else {
    setDataStatus("error");
  }

  return () => (isSubscribed = false);
}

export default function WidgetContent() {
  const [data, setData] = useState<any[] | undefined>(undefined);
  const [dataStatus, setDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");
  const [modalVisible, setModalVisible] = useState(false);
  const [modalData, setModalData] = useState<AlertModalData | undefined>(
    undefined,
  );

  const vmc = useContext(VehicleManagementContext);

  useEffect(() => {
    update(vmc.vehicle.locationVehicle, setData, setDataStatus);
  }, [vmc.vehicle.locationVehicle]);

  useEffect(() => {
    update(vmc.vehicle.locationVehicle, setData, setDataStatus);
  }, []);

  const onClickAlertViewButton = (viewData: any) => {
    setModalVisible(true);
    setModalData(viewData);
  };

  return (
    <div>
      <Table
        enableKeyboardNavigation={true}
        variant="borderless"
        resizableColumns={true}
        items={data ?? []}
        columnDefinitions={alertsDefinition(onClickAlertViewButton)}
        loadingText="Loading alerts"
        loading={dataStatus === "loading"}
        empty={
          <EmptyState
            title={"vehicle alerts"}
            description={"no alerts"}
          ></EmptyState>
        }
      />
      {modalData && (
        <DynamicModal
          title={modalData.title}
          content={{ type: modalData.type, data: modalData.data }}
          visible={modalVisible}
          setVisible={setModalVisible}
        />
      )}
    </div>
  );
}
