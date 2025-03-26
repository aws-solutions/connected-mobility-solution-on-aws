// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Box, Header, Link } from "@cloudscape-design/components";
import { WidgetConfig } from "../interfaces";
import { VehicleItem } from "@com.cms.fleetmanagement/api-client";
import { VehicleManagementContext } from "@/components/vehicles/vehicle-management/VehicleManagementContext";
import { GaugeComponent } from "react-gauge-component";
import { generateRandomDelay, generateRandomNumber } from "@/utils";

type SpeedData = {
  value: number;
  unit: string;
  timestamp: string;
};

export const vehicleSpeed: WidgetConfig = {
  definition: {
    defaultRowSpan: 4,
    defaultColumnSpan: 2,
    minRowSpan: 4,
    minColumnSpan: 2,
  },
  data: {
    icon: "table",
    title: "Vehicle Speed",
    description: "View current vehicle speed",
    disableContentPaddings: false,
    header: WidgetHeader,
    content: WidgetContent,
  },
};

function WidgetHeader() {
  return <Header>Vehicle Speed</Header>;
}

export const fetchVehicleSpeed = (): Promise<number> => {
  return new Promise((resolve, _) => {
    setTimeout(
      () => {
        resolve(generateRandomNumber(0, 60));
      },
      generateRandomDelay(1, 2),
    );
  });
};

let isSubscribed = true;
async function update(
  locationVehicle: VehicleItem | undefined,
  setData: React.Dispatch<React.SetStateAction<SpeedData | undefined>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (locationVehicle) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const vehicleSpeedInfo = {
        value: await fetchVehicleSpeed(),
        unit: "mph",
        timestamp: new Date().toISOString(),
      };

      if (isSubscribed) {
        setData(vehicleSpeedInfo);
      }
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
  const [data, setData] = useState<any>(undefined);
  const [dataStatus, setDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");

  const vmc = useContext(VehicleManagementContext);

  useEffect(() => {
    update(vmc.vehicle.locationVehicle, setData, setDataStatus);
  }, [vmc.vehicle.locationVehicle]);

  useEffect(() => {
    update(vmc.vehicle.locationVehicle, setData, setDataStatus);
  }, []);

  return (
    <div
      style={{
        height: "100%",
        width: "100%",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <GaugeComponent
        value={data ? data.value : 0}
        maxValue={160}
        minValue={0}
        labels={{
          valueLabel: {
            formatTextValue: (value) => `${value} mph`,
          },
          tickLabels: {
            type: "inner",
            ticks: [
              { value: 20 },
              { value: 40 },
              { value: 60 },
              { value: 80 },
              { value: 100 },
              { value: 120 },
              { value: 140 },
              { value: 160 },
            ],
          },
        }}
        pointer={{
          elastic: true,
          animationDelay: 0,
        }}
        arc={{
          colorArray: ["#5BE12C", "#EA4228"],
          subArcs: [{ limit: 60 }, { limit: 80 }, { limit: 160 }],
          padding: 0.02,
          width: 0.1,
        }}
        type="radial"
      />
    </div>
  );
}
