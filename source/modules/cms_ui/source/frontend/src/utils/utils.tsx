// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export function generateRandomDelay(minSec: number, maxSec: number) {
  const minMS = minSec * 1000;
  const maxMS = maxSec * 1000;

  return Math.floor(Math.random() * (maxMS - minMS + 1)) + minMS;
}

export function performRandomDelayAsync(minSec: number, maxSec: number) {
  const delay = generateRandomDelay(minSec, maxSec);
  return new Promise((resolve) => {
    setTimeout(resolve), delay;
  });
}

export function generateRandomNumber(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
