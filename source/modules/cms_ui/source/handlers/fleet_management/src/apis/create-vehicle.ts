// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CreateVehicleInput } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  CreateVehicleCommand,
  GetDecoderManifestCommand,
  VehicleAssociationBehavior,
} from "@aws-sdk/client-iotfleetwise";

export async function createVehicle(input: CreateVehicleInput): Promise<{}> {
  const client = new IoTFleetWiseClient();

  const getDecoderManifest = new GetDecoderManifestCommand({
    name: input.entry.decoderManifestName,
  });
  const decoderManifest = await client.send(getDecoderManifest);

  const createVehicleInput = {
    vehicleName: input.entry.name,
    modelManifestArn: decoderManifest.modelManifestArn,
    decoderManifestArn: decoderManifest.arn,
    associationBehavior: VehicleAssociationBehavior.CREATE_IOT_THING,
    attributes: {
      vin: input.entry.vin,
      make: input.entry.make,
      model: input.entry.model,
      year: `${input.entry.year}`,
      license: input.entry.licensePlate,
    },
    tags: input.entry.tags || [],
  };

  const command = new CreateVehicleCommand(createVehicleInput);
  await client.send(command);
  return;
}
