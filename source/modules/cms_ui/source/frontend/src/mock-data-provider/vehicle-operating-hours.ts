// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { generateRandomDelay } from "@/utils";

export type OperatingHoursDataItem = {
  date: Date;
  idle: number;
  charging: number;
  inOperation: number;
  inService: number;
};

export const fetchVehicleOperatingHours = (): Promise<
  OperatingHoursDataItem[] | undefined
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

const operatingHoursBaseData = [
  { idle: 56, charging: 35, inOperation: 2, inService: 7 },
  { idle: 60, charging: 32, inOperation: 1, inService: 7 },
  { idle: 60, charging: 30, inOperation: 2, inService: 8 },
  { idle: 47, charging: 42, inOperation: 2, inService: 9 },
  { idle: 69, charging: 24, inOperation: 2, inService: 5 },
  { idle: 59, charging: 32, inOperation: 1, inService: 8 },
  { idle: 69, charging: 24, inOperation: 2, inService: 5 },
  { idle: 59, charging: 32, inOperation: 1, inService: 8 },
  { idle: 47, charging: 42, inOperation: 2, inService: 9 },
  { idle: 69, charging: 24, inOperation: 2, inService: 5 },
  { idle: 59, charging: 32, inOperation: 1, inService: 8 },
];

function generateDataForVehicle(): OperatingHoursDataItem[] {
  const msPerDay = 24 * 60 * 60 * 1000;

  const startDate =
    new Date().getTime() - msPerDay * (operatingHoursBaseData.length - 1);

  const data = operatingHoursBaseData.map<OperatingHoursDataItem>(
    (value, i) => ({
      date: new Date(startDate + i * msPerDay),
      ...value,
    }),
  );

  return data;
}
