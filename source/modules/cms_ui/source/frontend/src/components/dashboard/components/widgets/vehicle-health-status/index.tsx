// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState, useEffect, useContext } from "react";
import { Header } from "@cloudscape-design/components";
import { commonChartProps } from "../chart-commons";
import { WidgetConfig } from "../interfaces";
import PieChart from "@cloudscape-design/components/pie-chart";
import Box from "@cloudscape-design/components/box";
import { FleetItem } from "@com.cms.fleetmanagement/api-client";
import {
  fetchVehicleHealth,
  VehicleHealthData,
} from "@/mock-data-provider/vehicle-health";
import { UserContext } from "@/components/commons/UserContext";
import { getDemoContextForFleet } from "@/api/mock/data/fleets-data";

export const vehicleHealthStatus: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2, minRowSpan: 3 },
  data: {
    icon: "pieChart",
    title: "Vehicle Health Status",
    description: "Current state of all fleet vehicles",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header variant="h2" description="Current state of all fleet vehicles">
      Vehicle Health Status
    </Header>
  );
}

let isSubscribed = true;
async function update(
  selectedFleet: FleetItem | null,
  setData: React.Dispatch<React.SetStateAction<VehicleHealthData[]>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
  setSum: React.Dispatch<React.SetStateAction<string>>,
) {
  if (selectedFleet) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const vehicleHealth = await fetchVehicleHealth(selectedFleet.id);
      if (isSubscribed) setData(vehicleHealth);
      let sum = 0;
      if (vehicleHealth != undefined) {
        vehicleHealth.forEach((x) => (sum += x.value));
      }

      setSum(sum.toString());
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
  const [data, setData] = useState<VehicleHealthData[]>([]);
  const [dataSum, setDataSum] = useState<string>("0");
  const [dataStatus, setDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");

  const uc = useContext(UserContext);

  useEffect(() => {
    update(
      getDemoContextForFleet(uc.fleet.selectedFleet, uc.demoMode.isDemoMode),
      setData,
      setDataStatus,
      setDataSum,
    );
  }, [uc.fleet.selectedFleet, uc.demoMode.isDemoMode]);

  useEffect(() => {
    update(
      getDemoContextForFleet(uc.fleet.selectedFleet, uc.demoMode.isDemoMode),
      setData,
      setDataStatus,
      setDataSum,
    );
  }, []);

  return (
    <PieChart
      {...commonChartProps}
      variant="donut"
      data={data}
      statusType={dataStatus}
      size="medium"
      loadingText="Fetching vehicle health"
      detailPopoverContent={(datum, sum) => [
        { key: "Vehicle count", value: datum.value },
        {
          key: "Percentage",
          value: `${((datum.value / sum) * 100).toFixed(0)}%`,
        },
      ]}
      segmentDescription={(datum, sum) =>
        `${datum.value} vehicles, ${((datum.value / sum) * 100).toFixed(0)}%`
      }
      innerMetricDescription="Vehicles"
      innerMetricValue={dataSum}
      hideFilter={true}
      hideLegend={true}
      fitHeight={true}
      ariaLabel="Fleet Vehicle Health"
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
            There is no vehicle health data available
          </Box>
        </Box>
      }
    />
  );
}
