// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { FleetManagementClient } from "@com.cms.fleetmanagement/api-client";
import { ApiConfig } from "./provider";
import { MockFleetManagementClient } from "./mock/client";

export const createFleetManagementClient = (
  config: ApiConfig,
  authToken: string,
): FleetManagementClient => {
  if (config.isDemoMode == "true") {
    const mockClient = new MockFleetManagementClient({
      endpoint: config.baseUrl,
    });
    return mockClient;
  }
  const client = new FleetManagementClient({
    endpoint: config.baseUrl,
    apiKey: { apiKey: authToken },
  });
  return client;
};
