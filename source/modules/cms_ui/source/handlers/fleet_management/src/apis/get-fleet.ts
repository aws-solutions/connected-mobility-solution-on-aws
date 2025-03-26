// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  CampaignStatus,
  CampaignTargetType,
  FleetItem,
  GetFleetInput,
  VehicleStatus,
  FleetNotFound,
} from "@com.cms.fleetmanagement/api-server";
import {
  GetFleetCommand,
  IoTFleetWiseClient,
  ListVehiclesInFleetCommand,
  ListTagsForResourceCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { getVehicleStatus } from "./utils";
import { listCampaignsForTarget } from "./list-campaigns-for-target";

export async function getFleet(input: GetFleetInput): Promise<FleetItem> {
  const client = new IoTFleetWiseClient();
  const getFleetCommand = new GetFleetCommand({ fleetId: input.id });
  try {
    const response = await client.send(getFleetCommand);
    const listTagsCommand = new ListTagsForResourceCommand({
      ResourceARN: response.arn,
    });
    const tags = await client.send(listTagsCommand);
    const campaigns = await listCampaignsForTarget({
      targetType: CampaignTargetType.FLEET,
      targetId: input.id,
    });
    const listVehiclesCommand = new ListVehiclesInFleetCommand({
      fleetId: input.id,
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
    return {
      id: response.id,
      name:
        tags.Tags.find((item) => item.Key === "DisplayName")?.Value ??
        response.id,
      numActiveCampaigns: campaigns.campaigns.filter(
        (campaign) => campaign.status === CampaignStatus.RUNNING,
      ).length,
      numTotalCampaigns: campaigns.campaigns.length,
      numConnectedVehicles: connectedVehicles.length,
      numTotalVehicles: vehicles.vehicles.length,
      createdTime: response.creationTime.toString(),
      lastModifiedTime: response.lastModificationTime.toString(),
      description: response?.description || "",
      tags: tags?.Tags || [],
    } as FleetItem;
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
