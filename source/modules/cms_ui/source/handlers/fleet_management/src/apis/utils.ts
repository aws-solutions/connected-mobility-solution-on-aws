// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { VehicleStatus } from "@com.cms.fleetmanagement/api-server";
import { IoTClient, ListThingPrincipalsCommand } from "@aws-sdk/client-iot";

export async function getVehicleStatus(
  vehicleName: string,
): Promise<VehicleStatus> {
  const client = new IoTClient();
  const command = new ListThingPrincipalsCommand({ thingName: vehicleName });
  const response = await client.send(command);
  if (response.principals.length > 0) {
    return VehicleStatus.ACTIVE;
  }
  return VehicleStatus.INACTIVE;
}
