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
  fetchDriverScores,
  ScoreData,
} from "@/mock-data-provider/driver-scores";
import { UserContext } from "@/components/commons/UserContext";
import { getDemoContextForFleet } from "@/api/mock/data/fleets-data";

export const fleetDriverScores: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2, minRowSpan: 3 },
  data: {
    icon: "pieChart",
    title: "Fleet Driver Scores",
    description: "Breakdown of driver scores across the fleet",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header
      variant="h2"
      description="Breakdown of driver scores across the fleet"
    >
      Fleet Driver Scores
    </Header>
  );
}

let isSubscribed = true;
async function update(
  selectedFleet: FleetItem | null,
  setData: React.Dispatch<React.SetStateAction<ScoreData[]>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (selectedFleet) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const driverScores = await fetchDriverScores(selectedFleet.id);
      if (isSubscribed) setData(driverScores);
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
  const [data, setData] = useState<ScoreData[]>([]);
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
    <PieChart
      {...commonChartProps}
      data={data}
      statusType={dataStatus}
      loadingText="Fetching driver scores"
      detailPopoverContent={(datum, sum) => [
        { key: "Driver count", value: datum.value },
        {
          key: "Percentage",
          value: `${((datum.value / sum) * 100).toFixed(0)}%`,
        },
      ]}
      segmentDescription={(datum, sum) =>
        `${datum.value} drivers, ${((datum.value / sum) * 100).toFixed(0)}%`
      }
      hideFilter={true}
      fitHeight={true}
      ariaLabel="Fleet Driver Scores"
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
            There is no driver score data available
          </Box>
        </Box>
      }
    />
  );
}
