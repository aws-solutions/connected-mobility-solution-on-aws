// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  EditVehicleInput,
  VehicleNotFound,
  VehicleBeingModified,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  UpdateVehicleCommand,
  ResourceNotFoundException,
  ConflictException,
  UpdateVehicleCommandInput,
  TagResourceCommand,
  TagResourceCommandInput,
  UpdateVehicleCommandOutput,
} from "@aws-sdk/client-iotfleetwise";

export async function editVehicle(input: EditVehicleInput): Promise<{}> {
  const client = new IoTFleetWiseClient();

  const editVehicleInput: UpdateVehicleCommandInput = {
    vehicleName: input.name,
    attributes: {
      vin: input.entry.vin,
      make: input.entry.make,
      model: input.entry.model,
      year: `${input.entry.year}`,
      license: input.entry.licensePlate,
    },
  };
  const command = new UpdateVehicleCommand(editVehicleInput);

  let updateVehicleResponse: UpdateVehicleCommandOutput;

  try {
    updateVehicleResponse = await client.send(command);
  } catch (e) {
    if (e instanceof ResourceNotFoundException) {
      throw new VehicleNotFound({
        message: "Vehicle not found.",
        vehicleName: input.name,
      });
    } else if (e instanceof ConflictException) {
      throw new VehicleBeingModified({
        message: "Vehicle undergoing modification now, try again in sometime.",
        vehicleName: input.name,
      });
    }
    throw e;
  }

  if (input.entry.tags != undefined) {
    const editVehicleTagsInput: TagResourceCommandInput = {
      ResourceARN: updateVehicleResponse.arn,
      Tags: input.entry.tags,
    };

    try {
      const editTagsCommand = new TagResourceCommand(editVehicleTagsInput);

      await client.send(editTagsCommand);
    } catch (e) {
      if (e instanceof ResourceNotFoundException) {
        throw new VehicleNotFound({
          message: "Vehicle not found.",
          vehicleName: input.name,
        });
      } else if (e instanceof ConflictException) {
        throw new VehicleBeingModified({
          message:
            "Vehicle tags are under modification now, try again in sometime.",
          vehicleName: input.name,
        });
      }
      throw e;
    }
  }

  return;
}
