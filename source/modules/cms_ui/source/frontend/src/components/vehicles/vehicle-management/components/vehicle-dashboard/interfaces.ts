// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

export interface StoredWidgetPlacement {
  id: string;
  columnOffset?: Record<number, number>;
  rowSpan?: number;
  columnSpan?: number;
}
