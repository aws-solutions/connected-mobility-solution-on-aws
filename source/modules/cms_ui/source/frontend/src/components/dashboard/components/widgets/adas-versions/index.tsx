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
import {
  fetchAdasVersionData,
  AdasVersionData,
} from "@/mock-data-provider/adas-versions";
import { UserContext } from "@/components/commons/UserContext";
import { FleetItem } from "@com.cms.fleetmanagement/api-client";
import { getDemoContextForFleet } from "@/api/mock/data/fleets-data";

export const adasVersions: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2, minRowSpan: 3 },
  data: {
    icon: "barChart",
    title: "ADAS Version",
    description: "Number of vehicles running various ADAS versions.",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header
      variant="h2"
      description="Number of vehicles running various ADAS versions."
    >
      ADAS Version
    </Header>
  );
}

let isSubscribed = true;
async function update(
  selectedFleet: FleetItem | null,
  setData: React.Dispatch<React.SetStateAction<AdasVersionData[]>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (selectedFleet) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const adasVersionData = await fetchAdasVersionData(selectedFleet.id);
      if (isSubscribed) setData(adasVersionData);
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
  const [data, setData] = useState<AdasVersionData[] | undefined>([]);
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

  function buildDomain(
    data: AdasVersionData[] | undefined,
  ): Date[] | undefined {
    if (data == undefined || data.length == 0) {
      return undefined;
    }

    return data.map(({ date }) => date);
  }

  function buildSeries(
    data: AdasVersionData[] | undefined,
  ): MixedLineBarChartProps.BarDataSeries<any>[] {
    if (data == null || data.length == 0) {
      return [];
    }

    return [
      {
        title: "# vehicles in v1.8.0",
        type: "bar",
        data: data.map((datum: AdasVersionData) => ({
          x: datum.date,
          y: datum["v1NumVehicles"],
        })),
      },
      {
        title: "# vehicles in v2.0.0",
        type: "bar",
        data: data.map((datum: AdasVersionData) => ({
          x: datum.date,
          y: datum["v2NumVehicles"],
        })),
      },
    ];
  }

  return (
    <BarChart
      {...commonChartProps}
      statusType={dataStatus}
      loadingText="Fetching ADAS versions"
      xDomain={buildDomain(data)}
      xScaleType="categorical"
      yDomain={[0, 175]}
      series={buildSeries(data)}
      stackedBars={true}
      xTitle="Date"
      yTitle="# vehicles"
      hideFilter={true}
      horizontalBars={true}
      fitHeight={true}
      height={15}
      ariaLabel="ADAS Software Version"
      detailPopoverSeriesContent={({ series, y }) => ({
        key: series.title,
        value: `${y} vehicles`,
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
            There is no ADAS version data available
          </Box>
        </Box>
      }
    />
  );
}
