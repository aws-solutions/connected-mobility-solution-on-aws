// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
export interface MetricsMessage {
  solution: string;
  uuid: string;
  timestamp: string;
  version: string;
  data: any;
}

export interface MetricsData {
  Type: string;
  [key: string]: string | number | boolean;
}

export const ACDP_METRICS_TYPE_CONSTANT = "AcdpBackstageMetrics";
