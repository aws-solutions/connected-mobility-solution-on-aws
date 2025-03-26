// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CreateFleetInput } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  CreateFleetCommand,
} from "@aws-sdk/client-iotfleetwise";

export async function createFleet(input: CreateFleetInput): Promise<{}> {
  const client = new IoTFleetWiseClient();
  const command = new CreateFleetCommand({
    fleetId: input.entry.id,
    description:
      input.entry?.description && input.entry.description.length > 0
        ? input.entry.description
        : undefined, //an empty string will fail validation, so need to reset back to undefined
    signalCatalogArn: input.entry.signalCatalogArn,
    tags: [
      { Key: "DisplayName", Value: input.entry.name },
      ...(input.entry?.tags || []),
    ],
  });
  await client.send(command);
  return;
}
