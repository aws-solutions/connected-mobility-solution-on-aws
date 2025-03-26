// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { generateRandomDelay } from "@/utils";
import { FLEETS } from "@/api/mock/data/fleets-data";

export type HardBrakingEventData = {
  date: Date;
  numEvents: number;
};

const hardBrakingEventsBaseData: Record<string, any[]> = {
  [FLEETS.TEST_FLEET_1]: [
    { numEvents: 4 },
    { numEvents: 2 },
    { numEvents: 3 },
    { numEvents: 2 },
    { numEvents: 4 },
    { numEvents: 3 },
    { numEvents: 8 },
    { numEvents: 7 },
    { numEvents: 9 },
    { numEvents: 10 },
    { numEvents: 9 },
  ],
  [FLEETS.TEST_FLEET_2]: [
    { numEvents: 4 },
    { numEvents: 2 },
    { numEvents: 3 },
    { numEvents: 2 },
    { numEvents: 4 },
    { numEvents: 3 },
    { numEvents: 8 },
    { numEvents: 7 },
    { numEvents: 9 },
    { numEvents: 10 },
    { numEvents: 9 },
  ],
};

export const fetchHardBrakingEvents = (
  fleetId: string,
): Promise<HardBrakingEventData[] | undefined> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        resolve(generateDataForVehicle(hardBrakingEventsBaseData[fleetId]));
      },
      generateRandomDelay(2, 5),
    );
  });
};

function generateDataForVehicle(
  hardBrakingData: { numEvents: number }[],
): HardBrakingEventData[] {
  if (hardBrakingData === undefined) {
    return [];
  }
  const msPerDay = 24 * 60 * 60 * 1000;

  const startDate =
    new Date().getTime() - msPerDay * (hardBrakingData.length - 1);

  const data = hardBrakingData.map<HardBrakingEventData>((value, i) => ({
    date: new Date(startDate + i * msPerDay),
    ...value,
  }));

  return data;
}
