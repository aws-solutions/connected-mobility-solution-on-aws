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
  fetchVehicleUtilization,
  UtilizationType,
  VehicleUtilizationData,
} from "@/mock-data-provider/vehicle-utilization";
import { UserContext } from "@/components/commons/UserContext";
import { getDemoContextForFleet } from "@/api/mock/data/fleets-data";

export const vehicleUtilization: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2, minRowSpan: 3 },
  data: {
    icon: "pieChart",
    title: "Vehicle Utilization",
    description: "Current utilization of all fleet vehicles",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header
      variant="h2"
      description="Current utilization of all fleet vehicles"
    >
      Vehicle Utilization Status
    </Header>
  );
}

let isSubscribed = true;
async function update(
  selectedFleet: FleetItem | null,
  setData: React.Dispatch<React.SetStateAction<VehicleUtilizationData[]>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
  setUtilizationAvg: React.Dispatch<React.SetStateAction<string>>,
) {
  if (selectedFleet) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const vehicleUtilization = await fetchVehicleUtilization(
        selectedFleet.id,
      );
      if (isSubscribed) setData(vehicleUtilization);
      let sumUsed = 0;
      let sumTotal = 0;

      if (vehicleUtilization) {
        vehicleUtilization.forEach((x) => {
          switch (x.utilized) {
            case UtilizationType.UTILIZED:
              sumUsed += x.value;
              sumTotal += x.value;
              break;
            case UtilizationType.NOT_UTILIZED:
              sumTotal += x.value;
              break;
            default:
              break;
          }
        });
        const utilizationAvg = `${Math.round(100 * (sumUsed / sumTotal))}%`;
        setUtilizationAvg(utilizationAvg);
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
  const [data, setData] = useState<VehicleUtilizationData[]>([]);
  const [utilizationAvg, setUtilizationAvg] = useState<string>("0%");
  const [dataStatus, setDataStatus] = useState<
    "loading" | "finished" | "error"
  >("loading");

  const uc = useContext(UserContext);

  useEffect(() => {
    update(
      getDemoContextForFleet(uc.fleet.selectedFleet, uc.demoMode.isDemoMode),
      setData,
      setDataStatus,
      setUtilizationAvg,
    );
  }, [uc.fleet.selectedFleet, uc.demoMode.isDemoMode]);

  useEffect(() => {
    update(
      getDemoContextForFleet(uc.fleet.selectedFleet, uc.demoMode.isDemoMode),
      setData,
      setDataStatus,
      setUtilizationAvg,
    );
  }, []);

  return (
    <PieChart
      {...commonChartProps}
      variant="donut"
      data={data}
      statusType={dataStatus}
      size="medium"
      loadingText="Fetching vehicle utilization"
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
      innerMetricDescription="Utilized"
      innerMetricValue={utilizationAvg}
      hideFilter={true}
      hideLegend={true}
      fitHeight={true}
      ariaLabel="Fleet Vehicle Utilization"
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
            There is no vehicle utilization data available
          </Box>
        </Box>
      }
    />
  );
}
