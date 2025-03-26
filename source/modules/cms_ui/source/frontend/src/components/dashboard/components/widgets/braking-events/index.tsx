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
  fetchHardBrakingEvents,
  HardBrakingEventData,
} from "@/mock-data-provider/hard-braking-events";
import { FleetItem } from "@com.cms.fleetmanagement/api-client";
import { UserContext } from "@/components/commons/UserContext";
import { getDemoContextForFleet } from "@/api/mock/data/fleets-data";

export const brakingEvents: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2, minRowSpan: 3 },
  data: {
    icon: "barChart",
    title: "Braking Events",
    description: "Daily number of hard braking events.",
    header: WidgetHeader,
    content: WidgetContent,
    staticMinHeight: 560,
  },
};

function WidgetHeader() {
  return (
    <Header variant="h2" description="Daily number of hard braking events.">
      Hard Braking Events
    </Header>
  );
}

let isSubscribed = true;
async function update(
  selectedFleet: FleetItem | null,
  setData: React.Dispatch<React.SetStateAction<HardBrakingEventData[]>>,
  setDataStatus: React.Dispatch<
    React.SetStateAction<"loading" | "finished" | "error">
  >,
) {
  if (selectedFleet) {
    isSubscribed = true;
    setDataStatus("loading");

    try {
      const hardBrakingEvents = await fetchHardBrakingEvents(selectedFleet.id);
      if (isSubscribed) setData(hardBrakingEvents);
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
  const [data, setData] = useState<HardBrakingEventData[] | undefined>([]);
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
    data: HardBrakingEventData[] | undefined,
  ): Date[] | undefined {
    if (data == undefined || data.length == 0) {
      return undefined;
    }

    return data.map(({ date }) => date);
  }

  function buildSeries(
    data: HardBrakingEventData[] | undefined,
  ): MixedLineBarChartProps.BarDataSeries<any>[] {
    if (data == null || data.length == 0) {
      return [];
    }

    return [
      {
        title: "# events",
        type: "bar",
        data: data.map((datum: HardBrakingEventData) => ({
          x: datum.date,
          y: datum["numEvents"],
        })),
      },
    ];
  }

  return (
    <BarChart
      {...commonChartProps}
      statusType={dataStatus}
      loadingText="Fetching braking events"
      xDomain={buildDomain(data)}
      xScaleType="categorical"
      yDomain={[0, 10]}
      series={buildSeries(data)}
      stackedBars={true}
      xTitle="Date"
      yTitle="# hard braking events"
      hideFilter={true}
      fitHeight={true}
      height={25}
      ariaLabel="Hard Braking Events"
      detailPopoverSeriesContent={({ series, y }) => ({
        key: series.title,
        value: `${y} events`,
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
            There is no hard braking events data available
          </Box>
        </Box>
      }
    />
  );
}
