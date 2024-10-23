// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { StatusType } from "@aws-sdk/client-codebuild";

import { StatusRunning, StatusOK, StatusAborted, StatusError } from "./Status";

interface BuildStatusProps {
  status?: string;
}

export const BuildStatus = (props: BuildStatusProps) => {
  switch (props.status) {
    case StatusType.IN_PROGRESS:
      return (
        <>
          <StatusRunning /> In progress
        </>
      );
    case StatusType.FAULT:
      return (
        <>
          <StatusError /> Fault
        </>
      );
    case StatusType.TIMED_OUT:
      return (
        <>
          <StatusError /> Timed out
        </>
      );
    case StatusType.FAILED:
      return (
        <>
          <StatusError /> Failed
        </>
      );
    case StatusType.SUCCEEDED:
      return (
        <>
          <StatusOK /> Succeeded
        </>
      );
    case StatusType.STOPPED:
      return (
        <>
          <StatusAborted /> Stopped
        </>
      );
    default:
      return (
        <>
          <StatusAborted /> Unknown
        </>
      );
  }
};
