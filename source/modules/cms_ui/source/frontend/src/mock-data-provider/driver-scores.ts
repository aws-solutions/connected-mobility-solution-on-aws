// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { generateRandomDelay } from "@/utils";
import { FLEETS } from "@/api/mock/data/fleets-data";

export type ScoreData = { title: string; value: number };

export const fetchDriverScores = (fleetId: string): Promise<ScoreData[]> => {
  return new Promise((resolve) => {
    setTimeout(
      () => {
        resolve(fleetDriverScoresData[fleetId]);
      },
      generateRandomDelay(2, 5),
    );
  });
};

const fleetDriverScoresData: Record<string, ScoreData[]> = {
  [FLEETS.TEST_FLEET_1]: [
    { title: "Risky", value: 2 },
    { title: "Needs Improvement", value: 10 },
    { title: "Below Average", value: 15 },
    { title: "Average", value: 25 },
    { title: "Excellent", value: 7 },
  ],
  [FLEETS.TEST_FLEET_2]: [
    { title: "Risky", value: 1 },
    { title: "Needs Improvement", value: 5 },
    { title: "Below Average", value: 12 },
    { title: "Average", value: 29 },
    { title: "Excellent", value: 10 },
  ],
};
