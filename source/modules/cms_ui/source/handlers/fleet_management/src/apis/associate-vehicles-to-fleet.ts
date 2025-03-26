// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  AssociateVehiclesToFleetInput,
  FleetNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  AssociateVehicleFleetCommand,
} from "@aws-sdk/client-iotfleetwise";

export async function associateVehiclesToFleet(
  input: AssociateVehiclesToFleetInput,
): Promise<{}> {
  const client = new IoTFleetWiseClient();
  await Promise.all(
    input.vehicleNames.map(async (vehicleName) => {
      const command = new AssociateVehicleFleetCommand({
        fleetId: input.id,
        vehicleName: vehicleName,
      });
      try {
        await client.send(command);
      } catch (e) {
        throw new FleetNotFound({
          message: `Error associating vehicle ${vehicleName} to fleet ${input.id}`,
          fleetId: input.id,
        });
      }
    }),
  );
  return {};
}
