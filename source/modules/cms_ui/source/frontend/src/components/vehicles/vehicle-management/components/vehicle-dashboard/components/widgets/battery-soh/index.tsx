// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState, useEffect, useContext } from "react";
import {
  Header,
  LineChart,
  MixedLineBarChartProps,
} from "@cloudscape-design/components";
import { commonChartProps } from "../chart-commons";
import { WidgetConfig } from "../interfaces";
import Box from "@cloudscape-design/components/box";
import {
  BatteryStateOfHealthDataItem,
  fetchVehicleBatteryStateOfHealth,
} from "@/mock-data-provider/battery-state-of-health";
import { VehicleManagementContext } from "@/components/vehicles/vehicle-management/VehicleManagementContext";
import { VehicleItem } from "@com.cms.fleetmanagement/api-client";

export const batteryStateOfHealth: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 1, minRowSpan: 3 },
  data: {
    icon: "lineChart",
    title: "Battery State of Health",
    description: "Actual battery current over time",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header variant="h2" description="Actual battery current over time">
      Battery State of Health
    </Header>
  );
}

let isSubscribed = true;
async function update(
  locationVehicle: VehicleItem | undefined,
  setData: React.Dispatch<
    React.SetStateAction<BatteryStateOfHealthDataItem[] | undefined>
  >,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (locationVehicle) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const batteryStateOfHealth = await fetchVehicleBatteryStateOfHealth();
      if (isSubscribed) setData(batteryStateOfHealth);

      setDataStatus("finished");
    } catch (e) {
      setDataStatus("error");
    }
  } else {
    setDataStatus("error");
  }

  return () => (isSubscribed = false);
}

function buildDomain(
  data: BatteryStateOfHealthDataItem[] | undefined,
): number[] | undefined {
  if (data == undefined || data.length == 0) {
    return undefined;
  }

  return [
    Math.min(...data.map((point) => point.value)) - 2,
    Math.max(...data.map((point) => point.value)) + 2,
  ];
}

function buildSeries(
  data: BatteryStateOfHealthDataItem[] | undefined,
): MixedLineBarChartProps.LineDataSeries<Date>[] {
  if (data == null || data.length == 0) {
    return [];
  }

  return [
    {
      title: "Battery Current",
      type: "line",
      data: data.map((datum: BatteryStateOfHealthDataItem) => ({
        x: datum.date,
        y: parseFloat(datum.value.toFixed(2)),
      })),
    },
  ];
}

export default function WidgetContent() {
  const [data, setData] = useState<BatteryStateOfHealthDataItem[] | undefined>(
    undefined,
  );
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
    <LineChart
      {...commonChartProps}
      statusType={dataStatus}
      loadingText="Fetching vehicle battery health"
      height={25}
      xTitle="Time"
      yTitle="Battery Current"
      xScaleType="time"
      yScaleType="linear"
      yDomain={buildDomain(data)}
      series={buildSeries(data)}
      i18nStrings={{
        ...commonChartProps.i18nStrings,
      }}
      xTickFormatter={(e) =>
        e
          ? e
              .toLocaleDateString("en-US", {
                hour: "numeric",
                minute: "numeric",
              })
              .split(",")
              .join("\n")
          : ""
      }
      yTickFormatter={function l(e) {
        return e ? e.toFixed(0) : "";
      }}
      hideFilter={true}
      fitHeight={true}
      ariaLabel="Vehicle Battery State of Health"
      empty={
        <Box textAlign="center" color="inherit">
          <b>No data available</b>
          <Box variant="p" color="inherit">
            There is no data available
          </Box>
        </Box>
      }
      noMatch={
        <Box textAlign="center" color="inherit">
          <b>No Data</b>
          <Box variant="p" color="inherit">
            There is no battery health data available
          </Box>
        </Box>
      }
    />
  );
}
