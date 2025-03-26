// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  DeleteVehicleInput,
  VehicleNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  DeleteVehicleCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { IoTClient, DeleteThingCommand } from "@aws-sdk/client-iot";

export async function deleteVehicle(input: DeleteVehicleInput): Promise<{}> {
  try {
    const fleetwiseClient = new IoTFleetWiseClient();
    const deleteVehicleCommand = new DeleteVehicleCommand({
      vehicleName: input.name,
    });
    await fleetwiseClient.send(deleteVehicleCommand);

    const iotClient = new IoTClient();
    const deleteThingCommand = new DeleteThingCommand({
      thingName: input.name,
    });
    await iotClient.send(deleteThingCommand);
    return;
  } catch (e) {
    if (e instanceof ResourceNotFoundException) {
      throw new VehicleNotFound({
        message: "Vehicle not found.",
        vehicleName: input.name,
      });
    }
    throw e;
  }
}
