// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CampaignTargetType,
  FleetItem,
  ListFleetsOutput,
  VehicleStatus,
} from "@com.cms.fleetmanagement/api-server";
import {
  CampaignStatus,
  IoTFleetWiseClient,
  ListFleetsCommand,
  ListVehiclesInFleetCommand,
  ListTagsForResourceCommand,
} from "@aws-sdk/client-iotfleetwise";
import { getVehicleStatus } from "./utils";
import { listCampaignsForTarget } from "./list-campaigns-for-target";

export async function listFleets(): Promise<ListFleetsOutput> {
  const client = new IoTFleetWiseClient();
  const input = {
    maxResults: 100,
  };
  const listFleetsCommand = new ListFleetsCommand(input);
  const response = await client.send(listFleetsCommand);
  const fleets = response.fleetSummaries.map(async (fleet) => {
    const campaigns = await listCampaignsForTarget({
      targetType: CampaignTargetType.FLEET,
      targetId: fleet.id,
    });
    const listVehiclesCommand = new ListVehiclesInFleetCommand({
      fleetId: fleet.id,
    });
    const vehicles = await client.send(listVehiclesCommand);
    const connectedVehicles = [];
    await Promise.all(
      vehicles.vehicles.map(async (vehicleName) => {
        const status = await getVehicleStatus(vehicleName);
        if (status === VehicleStatus.ACTIVE) {
          connectedVehicles.push(vehicleName);
        }
      }),
    );
    const listTagsCommand = new ListTagsForResourceCommand({
      ResourceARN: fleet.arn,
    });
    const tags = await client.send(listTagsCommand);
    return {
      id: fleet.id,
      name:
        tags.Tags?.find((item) => item.Key === "DisplayName")?.Value ??
        fleet.id,
      numActiveCampaigns: campaigns.campaigns.filter(
        (campaign) => campaign.status === CampaignStatus.RUNNING,
      ).length,
      numTotalCampaigns: campaigns.campaigns.length,
      numConnectedVehicles: connectedVehicles.length,
      numTotalVehicles: vehicles.vehicles.length,
      createdTime: fleet.creationTime.toString(),
      lastModifiedTime: fleet.lastModificationTime.toString(),
    } as FleetItem;
  });

  return {
    fleets: await Promise.all(fleets),
  };
}
