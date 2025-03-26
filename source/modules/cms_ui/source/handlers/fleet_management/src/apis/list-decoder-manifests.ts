// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  ListDecoderManifestsOutput,
  DecoderManifestItem,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ListDecoderManifestsCommand,
} from "@aws-sdk/client-iotfleetwise";

export async function listDecoderManifests(): Promise<ListDecoderManifestsOutput> {
  const client = new IoTFleetWiseClient();
  const command = new ListDecoderManifestsCommand();
  const response = await client.send(command);
  const decoderManifests = response.summaries.map(
    (decoderManifest) =>
      ({
        name: decoderManifest.name,
        arn: decoderManifest.arn,
        modelManifestArn: decoderManifest.modelManifestArn,
      }) as DecoderManifestItem,
  );
  return {
    decoderManifests: decoderManifests,
  };
}
