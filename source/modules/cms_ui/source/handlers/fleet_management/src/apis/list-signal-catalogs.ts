// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  ListSignalCatalogsOutput,
  SignalCatalogItem,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ListSignalCatalogsCommand,
} from "@aws-sdk/client-iotfleetwise";

export async function listSignalCatalogs(): Promise<ListSignalCatalogsOutput> {
  const client = new IoTFleetWiseClient();
  const command = new ListSignalCatalogsCommand();
  const response = await client.send(command);
  const signalCatalogs = response.summaries.map(
    (signalCatalog) =>
      ({
        name: signalCatalog.name,
        arn: signalCatalog.arn,
      }) as SignalCatalogItem,
  );
  return {
    signalCatalogs: signalCatalogs,
  };
}
