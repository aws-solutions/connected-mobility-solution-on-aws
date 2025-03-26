// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { BoardProps } from "@cloudscape-design/board-components/board";
import { StoredWidgetPlacement } from "./interfaces";
import { vehicleDetails, vehicleStatus } from "./components/widgets";
import {
  DashboardWidgetItem,
  WidgetConfig,
  WidgetDataType,
} from "./components/widgets/interfaces";
import { operatingHours } from "./components/widgets/operating-hours";
import { batteryStateOfHealth } from "./components/widgets/battery-soh";
import { vehicleAlerts } from "./components/widgets/vehicle-alerts";
import { vehicleLocationMap } from "./components/widgets/vehicle-location-map";
import { vehicleSpeed } from "./components/widgets/vehicle-speed";

export type { DashboardWidgetItem };
export { PaletteItem } from "./components/palette-item";

export const allWidgets: Record<string, WidgetConfig> = {
  vehicleDetails,
  vehicleStatus,
  operatingHours,
  batteryStateOfHealth,
  vehicleAlerts,
  vehicleLocationMap,
  vehicleSpeed,
};

const defaultLayout: ReadonlyArray<StoredWidgetPlacement> = [
  { id: "vehicleDetails", columnOffset: { "6": 0 }, columnSpan: 3 },
  { id: "vehicleStatus", columnOffset: { "6": 3 }, columnSpan: 1 },
  { id: "vehicleLocationMap", columnOffset: { "6": 4 }, columnSpan: 2 },
  { id: "operatingHours", columnOffset: { "6": 6 }, columnSpan: 2 },
  { id: "batteryStateOfHealth", columnOffset: { "6": 2 }, columnSpan: 2 },
  { id: "vehicleSpeed", columnOffset: { "6": 4 }, columnSpan: 2 },
  { id: "vehicleAlerts", columnOffset: { "6": 4 }, columnSpan: 4 },
];

function merge<T extends { id: string }>(
  src: ReadonlyArray<T>,
  overrides: ReadonlyArray<Partial<T> & { id: string }>,
): ReadonlyArray<T> {
  return src.map((item) => {
    const match = overrides.find((override) => override.id === item.id);
    return match ? { ...item, ...match } : item;
  });
}

export function getDefaultLayout(width: number) {
  if (width >= 2160) {
    // 6-col layout
    return merge(defaultLayout, [
      { id: "vehicleDetails", columnSpan: 4 },
      { id: "vehicleStatus", columnOffset: { "6": 4 }, columnSpan: 2 },
      { id: "operatingHours", columnOffset: { "6": 6 }, columnSpan: 2 },
      { id: "batteryStateOfHealth", columnOffset: { "6": 2 }, columnSpan: 2 },
      { id: "vehicleAlerts", columnOffset: { "6": 4 }, columnSpan: 4 },
    ]);
  }
  if (width > 1200) {
    return merge(defaultLayout, [
      {
        id: "vehicleDetails",
        columnSpan: 3,
        columnOffset: { "4": 0, 6: 0 },
        rowSpan: 2,
      },
      {
        id: "vehicleStatus",
        columnSpan: 1,
        columnOffset: { "4": 3, 6: 3 },
        rowSpan: 2,
      },
      {
        id: "operatingHours",
        columnSpan: 2,
        columnOffset: { "4": 0 },
        rowSpan: 4,
      },
      {
        id: "vehicleLocationMap",
        columnSpan: 2,
        columnOffset: { "4": 2 },
        rowSpan: 4,
      },
      {
        id: "batteryStateOfHealth",
        columnSpan: 2,
        columnOffset: { "4": 0 },
        rowSpan: 4,
      },
      {
        id: "vehicleAlerts",
        columnSpan: 4,
        columnOffset: { "4": 0 },
        rowSpan: 3,
      },
    ]);
  }
  if (width > 1045) {
    // 4-col layout with 4-col overview
    return defaultLayout;
  }
  if (width > 911) {
    // 4-col layout with 2-col overview
    return merge(defaultLayout, []);
  }
  if (width > 708) {
    // 2-col layout with 4-col overview
    return merge(defaultLayout, [
      { id: "vehicleDetails", columnOffset: { "6": 0 }, columnSpan: 3 },
      { id: "vehicleStatus", columnOffset: { "6": 3 }, columnSpan: 1 },
      { id: "operatingHours", columnOffset: { "6": 0 }, columnSpan: 2 },
      {
        id: "vehicleLocationMap",
        columnOffset: { "6": 2 },
        columnSpan: 2,
        rowSpan: 8,
      },
      { id: "batteryStateOfHealth", columnOffset: { "6": 0 }, columnSpan: 2 },
      { id: "vehicleAlerts", columnOffset: { "6": 4 }, columnSpan: 4 },
    ]);
  }
  if (width > 687) {
    // 2-col layout with 2-col overview
    return merge(defaultLayout, []);
  }
  if (width > 485) {
    // 1-col layout with 2-col overview
    return merge(defaultLayout, []);
  }
  // 1-col layout with 1-col overview
  return merge(defaultLayout, []);
}

export function exportLayout(
  items: ReadonlyArray<BoardProps.Item<WidgetDataType>>,
): ReadonlyArray<StoredWidgetPlacement> {
  return items.map((item) => ({
    id: item.id,
    columnSpan: item.columnSpan,
    columnOffset: item.columnOffset,
    rowSpan: item.rowSpan,
  }));
}

export function getBoardWidgets(layout: ReadonlyArray<StoredWidgetPlacement>) {
  return layout.map((position) => {
    const widget = allWidgets[position.id];
    return {
      ...position,
      ...widget,
      columnSpan:
        position.columnSpan ?? widget.definition?.defaultColumnSpan ?? 1,
      rowSpan: position.rowSpan ?? widget.definition?.defaultRowSpan ?? 2,
    };
  });
}

export function getPaletteWidgets(
  layout: ReadonlyArray<StoredWidgetPlacement>,
) {
  return Object.entries(allWidgets)
    .filter(([id]) => !layout.find((position) => position.id === id))
    .map(([id, widget]) => ({ id, ...widget }));
}
