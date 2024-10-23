// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Logger } from "winston";

// Log granular error message and error object.
// Throw generic error message with status code.
export async function awsApiCallWithErrorHandling<T>(
  apiCall: () => Promise<T>,
  customErrorMessage: string,
  logger: Logger,
): Promise<T> {
  try {
    return await apiCall();
  } catch (error: any) {
    if (typeof error.message === "string" && typeof error.statusCode === "number") {
      logger.error(`${customErrorMessage} Error: ${error}`);
      throw new Error(`Error while calling AWS API. Status Code: ${error.statusCode}`);
    } else {
      logger.error(`${customErrorMessage} Unexpected Error: ${error}`);
      throw new Error("Unexpected error while calling AWS API. Status code unknown.");
    }
  }
}