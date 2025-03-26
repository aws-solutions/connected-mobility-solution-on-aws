// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import { generateRandomDelay } from "@/utils";

export enum AlertViewType {
  TEXT = "text",
  IMAGE = "image",
  VIDEO = "video",
}

export interface AlertModalData {
  type: AlertViewType;
  data: string;
  title: string;
}

export const vehicleAlerts = [
  {
    id: "tire-pressure-warning-fp",
    name: "Tire Pressure",
    campaign: "Geo-Tracker",
    description: "Front passenger tire pressure warning",
    statusText: "Pending Fix",
    status: "pending",
    severity: "warning",
    severityText: "Medium",
    timestamp: new Date(),
    viewType: AlertViewType.TEXT,
    viewData:
      "The Front Tire Pressure warning alerts you when the air pressure in one or both of your vehicle's front tires drops below the recommended level. This critical safety feature monitors tire pressure continuously through sensors, helping prevent potential accidents and excessive tire wear caused by underinflation. When this warning appears on your dashboard, it indicates that immediate attention is needed to inspect and properly inflate the affected tire(s) to the manufacturer's specified pressure level, which can typically be found on the driver's side door jamb or in your owner's manual. Driving with underinflated tires not only compromises your vehicle's handling and braking performance but also reduces fuel efficiency and can lead to premature tire failure or blowouts at high speeds.",
  },
  {
    id: "hard-breaking-warning",
    name: "Hard Braking",
    campaign: "ADAS Collection",
    description: "Sudden and hard braking event",
    statusText: "Pending Fix",
    status: "pending",
    severity: "error",
    severityText: "High",
    timestamp: new Date(),
    viewType: AlertViewType.IMAGE,
    viewData: ["1", "2", "3"].map((n) => `/images/hard-braking-${n}.png`)[
      Math.floor(Math.random() * 3)
    ],
  },
  {
    id: "lane-departure",
    name: "Lane Departure",
    campaign: "ADAS Collection",
    description: "Vehicle departed lane boundary",
    statusText: "Pending Fix",
    status: "pending",
    severity: "warning",
    severityText: "Medium",
    timestamp: new Date(),
    viewType: AlertViewType.VIDEO,
    viewData: "/images/lane-departure-warning.mp4",
  },
];

export const fetchVehicleAlerts = (): Promise<any[] | undefined> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        resolve(vehicleAlerts);
      },
      generateRandomDelay(2, 5),
    );
  });
};
