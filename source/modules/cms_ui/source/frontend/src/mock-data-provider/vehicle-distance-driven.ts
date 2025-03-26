// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { generateRandomDelay } from "@/utils";
import { FLEETS } from "@/api/mock/data/fleets-data";

export type VehicleDistanceDrivenData = { x: Date; y: number };

export const fetchVehicleDistanceDriven = (
  fleetId: string,
): Promise<VehicleDistanceDrivenData[] | null> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        const distanceData = fleetDistanceData[fleetId];
        if (distanceData == undefined) resolve(null);
        else {
          resolve(generateDataForFleet(fleetDistanceData[fleetId]));
        }
      },
      generateRandomDelay(2, 5),
    );
  });
};

const fleetDistanceData: Record<string, number[]> = {
  [FLEETS.TEST_FLEET_1]: [
    3200, 4500, 3900, 4800, 5200, 4300, 3700, 5900, 4400, 5300, 4100, 3600,
    5700, 4800, 3400, 4000, 5500, 4600, 5000, 4200, 6100, 4500, 5300, 3900,
    5800, 4700, 3500, 6100, 4200, 4900,
  ],
  [FLEETS.TEST_FLEET_2]: [
    2300, 3400, 2900, 4100, 4900, 3800, 3000, 5400, 3600, 4200, 3900, 3100,
    5000, 4300, 3300, 4100, 5100, 3700, 4500, 3800, 5200, 4600, 4800, 4100,
    5500, 3900, 3200, 5800, 4100, 4700,
  ],
};

function generateDataForFleet(
  fleetData: number[],
): VehicleDistanceDrivenData[] {
  const msPerDay = 24 * 60 * 60 * 1000;
  const startDate = new Date().getTime() - msPerDay * (fleetData.length - 1);

  return fleetData.map<VehicleDistanceDrivenData>((value, i) => ({
    x: new Date(startDate + i * msPerDay),
    y: value,
  }));
}
