// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  DisassociateVehicleInput,
  VehicleNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  DisassociateVehicleFleetCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";

export async function disassociateVehicle(
  input: DisassociateVehicleInput,
): Promise<{}> {
  const client = new IoTFleetWiseClient();
  const command = new DisassociateVehicleFleetCommand({
    vehicleName: input.name,
    fleetId: input.fleetId,
  });
  try {
    await client.send(command);
    return;
  } catch (e) {
    if (e instanceof ResourceNotFoundException) {
      throw new VehicleNotFound({
        message: "Vehicle/fleet not found.",
        vehicleName: input.name,
      });
    }
    throw e;
  }
}
