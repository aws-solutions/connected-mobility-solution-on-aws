// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { generateRandomDelay } from "@/utils";
import { FLEETS } from "@/api/mock/data/fleets-data";

export type AdasVersionBaseData = {
  v1NumVehicles: number;
  v2NumVehicles: number;
};

export type AdasVersionData = {
  date: Date;
  v1NumVehicles: number;
  v2NumVehicles: number;
};

const adasVersionsBaseData = {
  [FLEETS.TEST_FLEET_1]: [
    { v1NumVehicles: 155, v2NumVehicles: 20 },
    { v1NumVehicles: 140, v2NumVehicles: 35 },
    { v1NumVehicles: 125, v2NumVehicles: 50 },
    { v1NumVehicles: 110, v2NumVehicles: 65 },
    { v1NumVehicles: 95, v2NumVehicles: 80 },
    { v1NumVehicles: 80, v2NumVehicles: 95 },
    { v1NumVehicles: 65, v2NumVehicles: 110 },
  ],
  [FLEETS.TEST_FLEET_2]: [
    { v1NumVehicles: 155, v2NumVehicles: 20 },
    { v1NumVehicles: 140, v2NumVehicles: 35 },
    { v1NumVehicles: 125, v2NumVehicles: 50 },
    { v1NumVehicles: 110, v2NumVehicles: 65 },
    { v1NumVehicles: 95, v2NumVehicles: 80 },
    { v1NumVehicles: 80, v2NumVehicles: 95 },
    { v1NumVehicles: 65, v2NumVehicles: 110 },
  ],
};

export const fetchAdasVersionData = (
  fleetId: string,
): Promise<AdasVersionData[] | undefined> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        resolve(generateDataForVehicle(adasVersionsBaseData[fleetId]));
      },
      generateRandomDelay(2, 5),
    );
  });
};

function generateDataForVehicle(
  adasVersionData: AdasVersionBaseData,
): AdasVersionData[] {
  if (adasVersionData === undefined) {
    return [];
  }
  const msPerDay = 24 * 60 * 60 * 1000;

  const startDate =
    new Date().getTime() - msPerDay * (adasVersionData.length - 1);

  const data = adasVersionData.map<AdasVersionData>((value, i) => ({
    date: new Date(startDate + i * msPerDay),
    ...value,
  }));

  return data;
}
