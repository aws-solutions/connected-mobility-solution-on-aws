// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState, useEffect, useContext } from "react";
import {
  AreaChart,
  Header,
  LineChart,
  Box,
  AreaChartProps,
} from "@cloudscape-design/components";
import { commonChartProps } from "../chart-commons";
import { WidgetConfig } from "../interfaces";
import { FleetItem } from "@com.cms.fleetmanagement/api-client";
import {
  fetchVehicleDistanceDriven,
  VehicleDistanceDrivenData,
} from "@/mock-data-provider/vehicle-distance-driven";
import { UserContext } from "@/components/commons/UserContext";
import { getDemoContextForFleet } from "@/api/mock/data/fleets-data";

export const vehicleDistanceDriven: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 1, minRowSpan: 3 },
  data: {
    icon: "lineChart",
    title: "Miles Driven per Day",
    description: "Miles driven per day over time for vehicles in a fleet",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header
      variant="h2"
      description="Miles driven per day over time for vehicles in a fleet"
    >
      Miles Driven per Day
    </Header>
  );
}

let isSubscribed = true;
async function update(
  selectedFleet: FleetItem | null,
  setData: React.Dispatch<
    React.SetStateAction<VehicleDistanceDrivenData[] | null>
  >,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (selectedFleet) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const vehicleDistanceDriven = await fetchVehicleDistanceDriven(
        selectedFleet.id,
      );
      if (isSubscribed) setData(vehicleDistanceDriven);
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
  const [data, setData] = useState<VehicleDistanceDrivenData[] | null>([]);
  const [dataStatus, setDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");

  const uc = useContext(UserContext);

  useEffect(() => {
    update(
      getDemoContextForFleet(uc.fleet.selectedFleet, uc.demoMode.isDemoMode),
      setData,
      setDataStatus,
    );
  }, [uc.fleet.selectedFleet, uc.demoMode.isDemoMode]);

  useEffect(() => {
    update(
      getDemoContextForFleet(uc.fleet.selectedFleet, uc.demoMode.isDemoMode),
      setData,
      setDataStatus,
    );
  }, []);

  function buildDomain(data: VehicleDistanceDrivenData[] | null) {
    if (data == null) {
      return undefined;
    }

    return [0, Math.max(...data.map((point) => point.y)) * 1.1];
  }

  function buildSeries(
    data: VehicleDistanceDrivenData[] | null,
  ): AreaChartProps.Series<VehicleDistanceDrivenData>[] {
    if (data == null) {
      return [];
    }

    return [
      {
        title: "Miles Driven",
        type: "area",
        data: data,
      },
    ];
  }

  return (
    <AreaChart
      {...commonChartProps}
      statusType={dataStatus}
      loadingText="Fetching vehicle distance driven"
      height={25}
      xTitle="Date"
      yTitle="Miles"
      xScaleType="time"
      yScaleType="linear"
      yDomain={buildDomain(data)}
      series={buildSeries(data)}
      i18nStrings={{
        xTickFormatter: (e) =>
          e
            .toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })
            .split(",")
            .join("\n"),
        yTickFormatter: function l(e) {
          return e.toFixed(0);
        },
      }}
      hideFilter={true}
      fitHeight={true}
      ariaLabel="Fleet Vehicle Distance Driven"
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
            There is no distance driven data available
          </Box>
        </Box>
      }
    />
  );
}
