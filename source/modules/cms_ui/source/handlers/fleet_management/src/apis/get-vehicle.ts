// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  VehicleNotFound,
  VehicleItem,
  VehicleAttributes,
  GetVehicleInput,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  GetVehicleCommand,
  ListTagsForResourceCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { getVehicleStatus } from "./utils";

export async function getVehicle(input: GetVehicleInput): Promise<VehicleItem> {
  const client = new IoTFleetWiseClient();
  const command = new GetVehicleCommand({ vehicleName: input.name });
  try {
    const response = await client.send(command);
    const listTagsCommand = new ListTagsForResourceCommand({
      ResourceARN: response.arn,
    });
    const tags = await client.send(listTagsCommand);
    const vehicle: VehicleItem = {
      name: response.vehicleName,
      status: await getVehicleStatus(input.name),
      attributes: {
        vin: response.attributes.vin,
        make: response.attributes.make,
        model: response.attributes.model,
        year: Number(response.attributes.year),
        licensePlate: response.attributes.license,
      } as VehicleAttributes,
      tags: tags?.Tags || [],
    } as VehicleItem;
    return vehicle;
  } catch (e) {
    if (e instanceof ResourceNotFoundException) {
      throw new VehicleNotFound({
        vehicleName: input.name,
        message: "Vehicle not found.",
      });
    }
    throw e;
  }
}
