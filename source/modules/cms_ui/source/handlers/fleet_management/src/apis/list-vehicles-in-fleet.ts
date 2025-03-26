// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  ListVehiclesInFleetInput,
  ListVehiclesInFleetOutput,
  VehicleItem,
} from "@com.cms.fleetmanagement/api-server";
import {
  GetVehicleCommand,
  IoTFleetWiseClient,
  ListVehiclesInFleetCommand,
} from "@aws-sdk/client-iotfleetwise";
import { getVehicleStatus } from "./utils";

export async function listVehiclesInFleet(
  input: ListVehiclesInFleetInput,
): Promise<ListVehiclesInFleetOutput> {
  const client = new IoTFleetWiseClient();
  const listVehiclesCommand = new ListVehiclesInFleetCommand({
    fleetId: input.id,
  });
  const vehicles = await client.send(listVehiclesCommand);
  const vehiclesInFleet = vehicles.vehicles.map(async (vehicleName) => {
    const getVehicleCommand = new GetVehicleCommand({
      vehicleName: vehicleName,
    });
    const getVehicleResponse = await client.send(getVehicleCommand);
    return {
      name: getVehicleResponse.vehicleName,
      status: await getVehicleStatus(vehicleName),
      attributes: {
        make: getVehicleResponse.attributes.make,
        model: getVehicleResponse.attributes.model,
        year: Number(getVehicleResponse.attributes.year),
        licensePlate: getVehicleResponse.attributes.license,
      },
    } as VehicleItem;
  });
  return { vehicles: await Promise.all(vehiclesInFleet) };
}
