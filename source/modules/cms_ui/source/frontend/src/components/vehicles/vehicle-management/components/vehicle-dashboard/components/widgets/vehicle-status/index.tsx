// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import Header from "@cloudscape-design/components/header";
import { WidgetConfig } from "../interfaces";
import {
  Link,
  KeyValuePairs,
  StatusIndicator,
} from "@cloudscape-design/components";
import {
  ListFleetsForVehicleCommand,
  VehicleItem,
  VehicleStatus,
} from "@com.cms.fleetmanagement/api-client";
import { VehicleManagementContext } from "@/components/vehicles/vehicle-management/VehicleManagementContext";
import { EmptyState } from "../../empty-state";
import { FleetSummary } from "@com.cms.fleetmanagement/api-client";
import { UI_ROUTES } from "@/utils/constants";
import { useNavigate } from "react-router-dom";
import { ApiContext } from "@/api/provider";

export const vehicleStatus: WidgetConfig = {
  definition: { defaultRowSpan: 2, defaultColumnSpan: 1 },
  data: {
    icon: "list",
    title: "Vehicle Status",
    description: "Current state of the vehicle",
    header: WidgetHeader,
    content: WidgetContent,
  },
};

function WidgetHeader() {
  return <Header variant="h2">Vehicle Status</Header>;
}

function WidgetContent() {
  const [data, setData] = useState<FleetSummary | null>(null);
  const [dataStatus, setDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");

  const vmc = useContext(VehicleManagementContext);
  const api = useContext(ApiContext);

  const vehicle = vmc.vehicle.locationVehicle;

  useEffect(() => {
    if (vehicle) {
      setDataStatus("loading");
      async function fetchFleetsForVehicle(vehicleName: string) {
        const cmd = new ListFleetsForVehicleCommand({ name: vehicleName });
        const output = await api.client.send(cmd);
        const selectedVehicleFleets = output.fleets || [];
        setData(
          selectedVehicleFleets.length > 0 ? selectedVehicleFleets[0] : null,
        );
        setDataStatus("finished");
      }
      fetchFleetsForVehicle(vehicle.name);
    } else {
      setDataStatus("error");
    }
  }, [vmc.vehicle.locationVehicle]);

  return vehicle === undefined ? (
    <EmptyState
      title={"vehicle"}
      description={"vehicle not found"}
    ></EmptyState>
  ) : (
    <KeyValuePairs
      columns={1}
      items={[
        {
          type: "group",
          items: [
            {
              label: "Fleet",
              value: vehicleFleet(dataStatus, data),
            },
            {
              label: "Vehicle Status",
              value: vehicleStatusIndicator(vehicle),
            },
          ],
        },
      ]}
    />
  );
}

const vehicleFleet = (
  dataStatus: "loading" | "finished" | "error",
  data: FleetSummary | null,
) => {
  const navigate = useNavigate();

  if (dataStatus === "loading") {
    return <StatusIndicator type={"loading"}>{"loading"}</StatusIndicator>;
  } else if (dataStatus === "finished") {
    return data ? (
      <Link
        onFollow={(event) => {
          event.preventDefault();
          navigate(`${UI_ROUTES.FLEET_MANAGEMENT}#${data.id}`);
        }}
      >
        {data?.name}
      </Link>
    ) : (
      "NOT ASSOCIATED"
    );
  } else {
    return <StatusIndicator type={"error"}>{"error"}</StatusIndicator>;
  }
};

const vehicleStatusIndicator = (item: VehicleItem) => {
  switch (item.status) {
    case VehicleStatus.ACTIVE:
      return <StatusIndicator type={"success"}>{item.status}</StatusIndicator>;
    case VehicleStatus.INACTIVE:
      return (
        <StatusIndicator type={"in-progress"}>{item.status}</StatusIndicator>
      );
    default:
      return <StatusIndicator type={"warning"}>{"unknown"}</StatusIndicator>;
  }
};
