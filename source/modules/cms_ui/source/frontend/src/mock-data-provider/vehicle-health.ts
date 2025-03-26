// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { generateRandomDelay } from "@/utils";
import { FLEETS } from "@/api/mock/data/fleets-data";

export type VehicleHealthData = { title: string; value: number };

export const fetchVehicleHealth = (
  fleetId: string,
): Promise<VehicleHealthData[]> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        resolve(fleetDriverScoresData[fleetId]);
      },
      generateRandomDelay(2, 5),
    );
  });
};

const fleetDriverScoresData: Record<string, VehicleHealthData[]> = {
  [FLEETS.TEST_FLEET_1]: [
    { title: "Action Soon", value: 128 },
    { title: "Action Now", value: 15 },
    { title: "Overdue", value: 7 },
    { title: "Up to Date", value: 25 },
  ],
  [FLEETS.TEST_FLEET_2]: [
    { title: "Action Soon", value: 17 },
    { title: "Action Now", value: 32 },
    { title: "Overdue", value: 2 },
    { title: "Up to Date", value: 120 },
  ],
};
