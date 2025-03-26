// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  EditFleetInput,
  FleetNotFound,
  FleetBeingModified,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  UpdateFleetCommand,
  TagResourceCommand,
  ResourceNotFoundException,
  ConflictException,
} from "@aws-sdk/client-iotfleetwise";

export async function editFleet(input: EditFleetInput): Promise<{}> {
  const client = new IoTFleetWiseClient();
  const command = new UpdateFleetCommand({
    fleetId: input.id,
    description:
      input.entry.description && input.entry.description.length > 0
        ? input.entry.description
        : undefined, //an empty string will fail validation, so need to reset back to undefined
  });

  try {
    const response = await client.send(command);
    const tagFleetCommand = new TagResourceCommand({
      ResourceARN: response.arn,
      Tags: [
        { Key: "DisplayName", Value: input.entry.name },
        ...input.entry.tags.filter((tag) => tag.Key !== "DisplayName"),
      ],
    });
    await client.send(tagFleetCommand);
    return;
  } catch (e) {
    if (e instanceof ResourceNotFoundException) {
      throw new FleetNotFound({
        message: "Fleet not found.",
        fleetId: input.id,
      });
    } else if (e instanceof ConflictException) {
      throw new FleetBeingModified({
        message: "Fleet undergoing modification now, try again in sometime.",
        fleetId: input.id,
      });
    }
    throw e;
  }
}
