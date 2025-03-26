// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState, useEffect, useContext } from "react";
import {
  Header,
  BarChart,
  MixedLineBarChartProps,
} from "@cloudscape-design/components";
import { commonChartProps, dateFormatter } from "../chart-commons";
import { WidgetConfig } from "../interfaces";
import Box from "@cloudscape-design/components/box";
import { VehicleItem } from "@com.cms.fleetmanagement/api-client";
import { VehicleManagementContext } from "@/components/vehicles/vehicle-management/VehicleManagementContext";
import {
  fetchVehicleOperatingHours,
  OperatingHoursDataItem,
} from "@/mock-data-provider/vehicle-operating-hours";

export const operatingHours: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2, minRowSpan: 3 },
  data: {
    icon: "barChart",
    title: "Operating Hours",
    description: "Daily hours by vehicle operation",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header variant="h2" description="Daily hours by vehicle operation">
      Operating Hours
    </Header>
  );
}

let isSubscribed = true;
async function update(
  locationVehicle: VehicleItem | undefined,
  setData: React.Dispatch<
    React.SetStateAction<OperatingHoursDataItem[] | undefined>
  >,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (locationVehicle) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const operatingHours = await fetchVehicleOperatingHours();
      if (isSubscribed) setData(operatingHours);
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
  const [data, setData] = useState<OperatingHoursDataItem[] | undefined>([]);
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

  function buildDomain(
    data: OperatingHoursDataItem[] | undefined,
  ): Date[] | undefined {
    if (data == undefined || data.length == 0) {
      return undefined;
    }

    return data.map(({ date }) => date);
  }

  function buildSeries(
    data: OperatingHoursDataItem[] | undefined,
  ): MixedLineBarChartProps.BarDataSeries<any>[] {
    if (data == null || data.length == 0) {
      return [];
    }

    return [
      {
        title: "Idle",
        type: "bar",
        data: data.map((datum: OperatingHoursDataItem) => ({
          x: datum.date,
          y: datum["idle"],
        })),
      },
      {
        title: "Charging",
        type: "bar",
        data: data.map((datum: OperatingHoursDataItem) => ({
          x: datum.date,
          y: datum["charging"],
        })),
      },
      {
        title: "In Operation",
        type: "bar",
        data: data.map((datum: OperatingHoursDataItem) => ({
          x: datum.date,
          y: datum["inOperation"],
        })),
      },
      {
        title: "In Service",
        type: "bar",
        data: data.map((datum: OperatingHoursDataItem) => ({
          x: datum.date,
          y: datum["inService"],
        })),
      },
    ];
  }

  return (
    <BarChart
      {...commonChartProps}
      statusType={dataStatus}
      loadingText="Fetching operating hours"
      xDomain={buildDomain(data)}
      xScaleType="categorical"
      yDomain={[0, 100]}
      series={buildSeries(data)}
      stackedBars={true}
      xTitle="Date"
      yTitle="% Operation"
      hideFilter={true}
      fitHeight={true}
      height={25}
      ariaLabel="Vehicle Operating Hours"
      detailPopoverSeriesContent={({ series, y }) => ({
        key: series.title,
        value: `${((y / 100) * 24).toFixed(1)} hours on ${series.title}`,
      })}
      i18nStrings={{
        ...commonChartProps.i18nStrings,
      }}
      xTickFormatter={dateFormatter}
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
            There is no operating hours data available
          </Box>
        </Box>
      }
    />
  );
}
