// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { IoTFleetWiseClient } from "@aws-sdk/client-iotfleetwise";
import { listSignalCatalogs } from "../list-signal-catalogs";

// Mock the AWS SDK clients
jest.mock("@aws-sdk/client-iotfleetwise");

describe("listSignalCatalogs", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should return a list of signal catalogs", async () => {
    // Mock data
    const mockSignalCatalogSummaries = [
      {
        name: "signal-catalog-1",
        arn: "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/signal-catalog-1",
      },
      {
        name: "signal-catalog-2",
        arn: "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/signal-catalog-2",
      },
    ];

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      summaries: mockSignalCatalogSummaries,
    });

    // Execute
    const result = await listSignalCatalogs();

    // Verify
    expect(result).toEqual({
      signalCatalogs: [
        {
          name: "signal-catalog-1",
          arn: "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/signal-catalog-1",
        },
        {
          name: "signal-catalog-2",
          arn: "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/signal-catalog-2",
        },
      ],
    });

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });

  it("should handle empty signal catalogs list", async () => {
    // Mock empty response
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      summaries: [],
    });

    // Execute
    const result = await listSignalCatalogs();

    // Verify
    expect(result).toEqual({ signalCatalogs: [] });
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });
});
