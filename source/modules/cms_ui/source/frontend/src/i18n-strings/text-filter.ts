// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export const getTextFilterCounterText = (count: number | undefined) =>
  `${count ?? 0} ${count === 1 ? "match" : "matches"}`;
