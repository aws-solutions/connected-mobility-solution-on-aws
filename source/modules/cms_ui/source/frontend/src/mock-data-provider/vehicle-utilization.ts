// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { generateRandomDelay } from "@/utils";
import { FLEETS } from "@/api/mock/data/fleets-data";

export enum UtilizationType {
  UTILIZED = "UTILIZED",
  NOT_UTILIZED = "NOT_UTILIZED",
  NOT_REPORTED = "NOT_REPORTED",
}

export type VehicleUtilizationData = {
  title: string;
  value: number;
  utilized: UtilizationType;
};

export const fetchVehicleUtilization = (
  fleetId: string,
): Promise<VehicleUtilizationData[]> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        resolve(fleetDriverScoresData[fleetId]);
      },
      generateRandomDelay(2, 5),
    );
  });
};

const fleetDriverScoresData: Record<string, VehicleUtilizationData[]> = {
  [FLEETS.TEST_FLEET_1]: [
    {
      title: "Vehicles not included",
      value: 3,
      utilized: UtilizationType.NOT_REPORTED,
    },
    {
      title: "Vehicles Off for > 24 hours",
      value: 64,
      utilized: UtilizationType.NOT_UTILIZED,
    },
    {
      title: "Vehicles On in last 24 hours",
      value: 107,
      utilized: UtilizationType.UTILIZED,
    },
  ],
  [FLEETS.TEST_FLEET_2]: [
    {
      title: "Vehicles not included",
      value: 2,
      utilized: UtilizationType.NOT_REPORTED,
    },
    {
      title: "Vehicles Off for > 24 hours",
      value: 73,
      utilized: UtilizationType.NOT_UTILIZED,
    },
    {
      title: "Vehicles On in last 24 hours",
      value: 96,
      utilized: UtilizationType.UTILIZED,
    },
  ],
};
