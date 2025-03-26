// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import Header from "@cloudscape-design/components/header";
import { WidgetConfig } from "../interfaces";
import { Link, KeyValuePairs } from "@cloudscape-design/components";
import { VehicleManagementContext } from "@/components/vehicles/vehicle-management/VehicleManagementContext";
import { EmptyState } from "../../empty-state";
import { VehicleItem } from "@com.cms.fleetmanagement/api-client";

export const vehicleDetails: WidgetConfig = {
  definition: { defaultRowSpan: 2, defaultColumnSpan: 2 },
  data: {
    icon: "list",
    title: "Vehicle details",
    description: "General information about the vehicle",
    header: WidgetHeader,
    content: WidgetContent,
  },
};

function WidgetHeader() {
  return <Header variant="h2">Vehicle Details</Header>;
}

let isSubscribed = true;
async function update(
  selectedVehicle: VehicleItem | undefined,
  setData: React.Dispatch<React.SetStateAction<VehicleItem | null>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (selectedVehicle) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      // const vehicleDetails = await fetchVehicleDetails(selectedVehicle.vehicleName);
      if (isSubscribed) setData(selectedVehicle);
      setDataStatus("finished");
    } catch (e) {
      setDataStatus("error");
    }
  } else {
    setDataStatus("error");
  }

  return () => (isSubscribed = false);
}

function WidgetContent() {
  const [data, setData] = useState<VehicleItem | null>(null);
  const [dataStatus, setDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");

  const vmc = useContext(VehicleManagementContext);

  useEffect(() => {
    update(vmc.vehicle.locationVehicle, setData, setDataStatus);
  }, [vmc.vehicle.locationVehicle]);

  const vehicle = vmc.vehicle.locationVehicle;

  return vehicle === undefined ? (
    <EmptyState
      title={"vehicle"}
      description={"vehicle not found"}
    ></EmptyState>
  ) : (
    <KeyValuePairs
      columns={3}
      items={[
        {
          type: "group",
          items: [
            {
              label: "Vehicle Name",
              value: vehicle.name,
            },
            {
              label: "Year / Make / Model",
              value: `${vehicle.attributes?.year} ${vehicle.attributes?.make} ${vehicle.attributes?.model}`,
            },
          ],
        },
        {
          type: "group",
          items: [
            {
              label: "License Plate",
              value: vehicle.attributes?.licensePlate,
            },
          ],
        },
        {
          type: "group",
          items: [
            {
              label: "Created",
              value: new Date().toISOString(),
            },
            {
              label: "Last Modified",
              value: new Date().toISOString(),
            },
          ],
        },
      ]}
    />
  );
}
