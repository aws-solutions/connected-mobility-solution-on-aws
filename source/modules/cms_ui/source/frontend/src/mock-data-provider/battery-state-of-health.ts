// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { generateRandomDelay } from "@/utils";
import { FLEETS } from "@/api/mock/data/fleets-data";

export type BatteryStateOfHealthDataItem = { date: Date; value: number };
export type FleetBatteryStateOfHealthData = {
  actual: BatteryStateOfHealthDataItem[];
  expected: BatteryStateOfHealthDataItem[];
};

export const fetchFleetBatteryStateOfHealth = (
  fleetId: string,
): Promise<{
  actual: BatteryStateOfHealthDataItem[];
  expected: BatteryStateOfHealthDataItem[];
} | null> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        const batteryHealthDataForFleet = batteryHealthData[fleetId];
        if (batteryHealthDataForFleet == undefined) resolve(null);
        else {
          resolve(generateDataForFleetWithExpected(batteryHealthData[fleetId]));
        }
      },
      generateRandomDelay(2, 5),
    );
  });
};

export const fetchVehicleBatteryStateOfHealth = (): Promise<
  BatteryStateOfHealthDataItem[] | undefined
> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        resolve(generateDataForVehicle());
      },
      generateRandomDelay(2, 5),
    );
  });
};

const batteryHealthData: Record<string, number[]> = {
  [FLEETS.TEST_FLEET_1]: [
    96.3, 94.1, 93.0, 91.4, 90.2, 89.3, 88.1, 87.2, 85.3, 84.1, 83.5, 82.9,
  ],
  [FLEETS.TEST_FLEET_2]: [
    95.8, 93.4, 92.3, 90.8, 89.5, 88.4, 86.9, 85.2, 84.3, 82.7, 81.4, 80.1,
  ],
};

function generateDataForFleetWithExpected(fleetData: number[]): {
  actual: BatteryStateOfHealthDataItem[];
  expected: BatteryStateOfHealthDataItem[];
} {
  const msPerMonth = 30 * 24 * 60 * 60 * 1000; // Approximate milliseconds in a month
  const startDate = new Date().getTime() - msPerMonth * (fleetData.length - 1);

  // Generate `actual` data from `batteryHealthData` for the selected fleet
  const actualData = fleetData.map<BatteryStateOfHealthDataItem>(
    (value, i) => ({
      date: new Date(startDate + i * msPerMonth),
      value: value,
    }),
  );

  // Generate `expected` data as a linear decline from 98.0% to 89.0%
  const expectedDeclineStart = 98.0;
  const expectedDeclineEnd = 78.0;
  const expectedData = Array.from({ length: fleetData.length }, (_, i) => {
    const monthProgress = i / (fleetData.length - 1);
    const expectedValue =
      expectedDeclineStart -
      (expectedDeclineStart - expectedDeclineEnd) * monthProgress;
    return {
      date: new Date(startDate + i * msPerMonth),
      value: parseFloat(expectedValue.toFixed(1)),
    };
  });

  return { actual: actualData, expected: expectedData };
}

const generateDataForVehicle = (): BatteryStateOfHealthDataItem[] => {
  const now = new Date();
  const interval = 1000; // 1-second intervals
  const totalPoints = 2 * 60 * 60; // 2 hours worth of data (60 seconds per minute * 60 minutes per hour)

  return Array.from({ length: totalPoints }, (_, i) => {
    const date = new Date(now.getTime() - (totalPoints - i) * interval);
    // Simulate fluctuation between 6 and 8 amps
    const baseValue = 7 + Math.sin(date.getTime() / (10 * 1000)); // Smooth sinusoidal fluctuation
    const noise = generateGaussianNoise(0, 1); // Gaussian noise with mean 0 and standard deviation 1
    const value = baseValue + noise; // Add Gaussian noise to the base value
    return { date, value };
  });
};

function generateGaussianNoise(mean: number, stdDev: number): number {
  const u1 = Math.random();
  const u2 = Math.random();
  const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  return z0 * stdDev + mean;
}
