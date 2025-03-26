// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CampaignTargetType,
  DeleteFleetInput,
  FleetNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  DeleteFleetCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { listCampaignsForTarget } from "./list-campaigns-for-target";
import { listVehiclesInFleet } from "./list-vehicles-in-fleet";
import { deleteCampaign } from "./delete-campaign";
import { disassociateVehicle } from "./disassociate-vehicle";

export async function deleteFleet(input: DeleteFleetInput): Promise<{}> {
  const client = new IoTFleetWiseClient();

  const campaigns = await listCampaignsForTarget({
    targetId: input.id,
    targetType: CampaignTargetType.FLEET,
  });
  Promise.all(
    campaigns.campaigns.map(async (campaign) => {
      await deleteCampaign({ name: campaign.name });
    }),
  );

  const vehicles = await listVehiclesInFleet({ id: input.id });
  Promise.all(
    vehicles.vehicles.map(async (vehicle) => {
      await disassociateVehicle({ name: vehicle.name, fleetId: input.id });
    }),
  );

  const command = new DeleteFleetCommand({
    fleetId: input.id,
  });

  try {
    await client.send(command);
    return;
  } catch (e) {
    if (e instanceof ResourceNotFoundException) {
      throw new FleetNotFound({
        message: "Fleet not found.",
        fleetId: input.id,
      });
    }
    throw e;
  }
}
