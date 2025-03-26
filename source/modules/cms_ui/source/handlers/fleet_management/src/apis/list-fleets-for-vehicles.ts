// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  ListFleetsForVehicleInput,
  ListFleetsForVehicleOutput,
  VehicleNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ListFleetsForVehicleCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";

export async function listFleetsForVehicle(
  input: ListFleetsForVehicleInput,
): Promise<ListFleetsForVehicleOutput> {
  const client = new IoTFleetWiseClient();
  const listFleetsForVehicleCommand = new ListFleetsForVehicleCommand({
    vehicleName: input.name,
  });
  try {
    const fleets = await client.send(listFleetsForVehicleCommand);
    return {
      fleets: fleets.fleets.map((fleetId) => ({
        id: fleetId,
        name: fleetId,
      })),
    };
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
