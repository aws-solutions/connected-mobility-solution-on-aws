// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { baseTableAriaLabels } from "@/i18n-strings";
import { TableProps } from "@cloudscape-design/components";

export const campaignTableAriaLabels: TableProps.AriaLabels<{ id: string }> = {
  ...baseTableAriaLabels,
  itemSelectionLabel: (data, row) => `select ${row.id}`,
  selectionGroupLabel: "Fleet selection",
};
