// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import {
  Box,
  SpaceBetween,
  ProgressBar,
  StatusIndicator,
  Flashbar,
} from "@cloudscape-design/components";

export type StatusType = "success" | "in-progress" | "pending" | "error";

export interface CreateVehicleProgressStep {
  label: String;
  status: StatusType;
}

export interface CreateVehicleProgressProps {
  steps: Record<string, CreateVehicleProgressStep>;
}

const getStatusIcon = (status: StatusType) => {
  switch (status) {
    case "success":
      return <StatusIndicator type="success">Complete</StatusIndicator>;
    case "in-progress":
      return <StatusIndicator type="in-progress">In progress</StatusIndicator>;
    case "pending":
      return <StatusIndicator type="pending">Pending</StatusIndicator>;
    case "error":
      return <StatusIndicator type="error">Error</StatusIndicator>;
    default:
      return null;
  }
};

export const CreateVehicleProgress = ({
  steps,
}: CreateVehicleProgressProps) => {
  return (
    <Box padding="l">
      <SpaceBetween size="l">
        <Flashbar
          items={[
            {
              content: (
                <ProgressBar
                  value={
                    (Object.values(steps).filter(
                      (step) => step.status === "success",
                    ).length /
                      Object.keys(steps).length) *
                    100
                  }
                  label="Overall progress"
                  description={`Step ${
                    Object.values(steps).filter(
                      (step) => step.status === "success",
                    ).length
                  } of ${Object.keys(steps).length}`}
                  variant="flash"
                />
              ),
              type: "in-progress",
              dismissible: false,
            },
          ]}
        />
        {Object.values(steps).map((step) => (
          <SpaceBetween size="xs" direction="horizontal" key={step.label}>
            {getStatusIcon(step.status)}
            <span>{step.label}</span>
          </SpaceBetween>
        ))}
      </SpaceBetween>
    </Box>
  );
};
