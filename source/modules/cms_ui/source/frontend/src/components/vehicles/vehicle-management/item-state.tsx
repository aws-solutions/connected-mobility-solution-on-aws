// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { StatusIndicator } from "@cloudscape-design/components";

export default function ItemState({ state }: any) {
  if (state === "deleting") {
    return <StatusIndicator type="pending">Deleting...</StatusIndicator>;
  }
  return (
    <StatusIndicator type={state === "Deactivated" ? "error" : "success"}>
      {state}
    </StatusIndicator>
  );
}
