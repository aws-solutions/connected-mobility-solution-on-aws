// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { BoardProps } from "@cloudscape-design/board-components/board";
import { StoredWidgetPlacement } from "./interfaces";
import {
  fleetDriverScores,
  vehicleHealthStatus,
  vehicleUtilization,
  vehicleDistanceDriven,
  batteryStateOfHealth,
  brakingEvents,
  adasVersions,
} from "./components/widgets";
import {
  DashboardWidgetItem,
  WidgetConfig,
  WidgetDataType,
} from "./components/widgets/interfaces";

export type { DashboardWidgetItem };
export { PaletteItem } from "./components/palette-item";

export const allWidgets: Record<string, WidgetConfig> = {
  fleetDriverScores,
  vehicleHealthStatus,
  vehicleUtilization,
  vehicleDistanceDriven,
  batteryStateOfHealth,
  brakingEvents,
  adasVersions,
};

const defaultLayout: ReadonlyArray<StoredWidgetPlacement> = [
  { id: "fleetDriverScores" },
  { id: "vehicleHealthStatus" },
  { id: "vehicleUtilization" },
  { id: "vehicleDistanceDriven" },
  { id: "batteryStateOfHealth" },
  { id: "brakingEvents" },
  { id: "adasVersions" },
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
      { id: "fleetDriverScores", columnOffset: { "6": 0 } },
      { id: "vehicleHealthStatus", columnOffset: { "6": 2 } },
      { id: "vehicleUtilization", columnOffset: { "6": 4 } },
      { id: "vehicleDistanceDriven", columnOffset: { "6": 0 }, columnSpan: 2 },
      { id: "batteryStateOfHealth", columnOffset: { "6": 2 }, columnSpan: 2 },
    ]);
  }
  if (width > 1045) {
    // 4-col layout with 4-col overview
    return defaultLayout;
  }
  if (width > 911) {
    // 4-col layout with 2-col overview
    return merge(defaultLayout, [{ id: "fleetDriverScores", rowSpan: 3 }]);
  }
  if (width > 708) {
    // 2-col layout with 4-col overview
    return merge(defaultLayout, [{ id: "fleetDriverScores", columnSpan: 2 }]);
  }
  if (width > 687) {
    // 2-col layout with 2-col overview
    return merge(defaultLayout, [{ id: "fleetDriverScores", columnSpan: 2 }]);
  }
  if (width > 485) {
    // 1-col layout with 2-col overview
    return merge(defaultLayout, [{ id: "fleetDriverScores", columnSpan: 2 }]);
  }
  // 1-col layout with 1-col overview
  return merge(defaultLayout, [{ id: "fleetDriverScores", rowSpan: 5 }]);
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
