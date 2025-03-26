// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  ListVehiclesOutput,
  VehicleItem,
  VehicleAttributes,
  VehicleStatus,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ListVehiclesCommand,
} from "@aws-sdk/client-iotfleetwise";
import { getVehicleStatus } from "./utils";

export async function listVehicles(): Promise<ListVehiclesOutput> {
  const client = new IoTFleetWiseClient();
  const input = {
    maxResults: 100,
  };
  const command = new ListVehiclesCommand(input);
  const response = await client.send(command);
  const vehicles = Promise.all(
    response.vehicleSummaries.map(async (vehicle) => {
      return {
        name: vehicle.vehicleName,
        status: await getVehicleStatus(vehicle.vehicleName),
        attributes: {
          vin: vehicle.attributes.vin,
          make: vehicle.attributes.make,
          model: vehicle.attributes.model,
          year: Number(vehicle.attributes.year),
          licensePlate: vehicle.attributes.license,
        } as VehicleAttributes,
      } as VehicleItem;
    }),
  );
  return {
    vehicles: await vehicles,
  };
}
