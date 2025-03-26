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
import { FleetItem } from "@com.cms.fleetmanagement/api-client";
import {
  FleetBatteryStateOfHealthData,
  fetchFleetBatteryStateOfHealth,
} from "@/mock-data-provider/battery-state-of-health";
import { UserContext } from "@/components/commons/UserContext";
import { getDemoContextForFleet } from "@/api/mock/data/fleets-data";

export const batteryStateOfHealth: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 1, minRowSpan: 3 },
  data: {
    icon: "lineChart",
    title: "Battery State of Health",
    description: "Average battery state of health over time for a fleet",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header
      variant="h2"
      description="Average battery state of health over time for a fleet"
    >
      Battery State of Health
    </Header>
  );
}

let isSubscribed = true;
async function update(
  selectedFleet: FleetItem | null,
  setData: React.Dispatch<
    React.SetStateAction<FleetBatteryStateOfHealthData | null>
  >,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (selectedFleet) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const batteryStateOfHealth = await fetchFleetBatteryStateOfHealth(
        selectedFleet.id,
      );
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

function generateSeries(
  data: FleetBatteryStateOfHealthData,
): MixedLineBarChartProps.LineDataSeries<Date>[] {
  if (!data) return [];

  return [
    {
      title: "Fleet Avg",
      type: "line",
      data: data
        ? data.actual.map((datum) => {
            return { x: datum.date, y: datum.value };
          })
        : [],
    },
    {
      title: "Expected Avg",
      type: "line",
      data: data
        ? data.expected.map((datum) => {
            return { x: datum.date, y: datum.value };
          })
        : [],
    },
  ];
}

export default function WidgetContent() {
  const [data, setData] = useState<FleetBatteryStateOfHealthData | null>(null);
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

  return (
    <LineChart
      {...commonChartProps}
      statusType={dataStatus}
      loadingText="Fetching fleet battery health"
      height={25}
      xTitle="Battery SoH over Time (Fleet Avg)"
      yTitle="SoH (%)"
      xScaleType="time"
      yScaleType="linear"
      yDomain={
        data
          ? [
              Math.min(...data.actual.map((point) => point.value)) * 0.9,
              Math.max(...data.actual.map((point) => point.value)) * 1.1,
            ]
          : undefined
      }
      series={generateSeries(data)}
      i18nStrings={{
        xTickFormatter: (e) =>
          e
            ? e
                .toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "short",
                })
                .split(",")
                .join("\n")
            : "",
        yTickFormatter: function l(e) {
          return e ? e.toFixed(0) : "";
        },
      }}
      hideFilter={true}
      fitHeight={true}
      ariaLabel="Fleet Vehicle Battery State of Health"
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
