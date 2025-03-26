// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { IoTFleetWiseClient } from "@aws-sdk/client-iotfleetwise";
import { listDecoderManifests } from "../list-decoder-manifests";

// Mock the AWS SDK clients
jest.mock("@aws-sdk/client-iotfleetwise");

describe("listDecoderManifests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should return a list of decoder manifests", async () => {
    // Mock data
    const mockDecoderManifestSummaries = [
      {
        name: "decoder-manifest-1",
        arn: "arn:aws:iotfleetwise:us-east-1:123456789012:decoder-manifest/decoder-manifest-1",
        modelManifestArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/model-manifest-1",
      },
      {
        name: "decoder-manifest-2",
        arn: "arn:aws:iotfleetwise:us-east-1:123456789012:decoder-manifest/decoder-manifest-2",
        modelManifestArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/model-manifest-2",
      },
    ];

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      summaries: mockDecoderManifestSummaries,
    });

    // Execute
    const result = await listDecoderManifests();

    // Verify
    expect(result).toEqual({
      decoderManifests: [
        {
          name: "decoder-manifest-1",
          arn: "arn:aws:iotfleetwise:us-east-1:123456789012:decoder-manifest/decoder-manifest-1",
          modelManifestArn:
            "arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/model-manifest-1",
        },
        {
          name: "decoder-manifest-2",
          arn: "arn:aws:iotfleetwise:us-east-1:123456789012:decoder-manifest/decoder-manifest-2",
          modelManifestArn:
            "arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/model-manifest-2",
        },
      ],
    });

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });

  it("should handle empty decoder manifests list", async () => {
    // Mock empty response
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      summaries: [],
    });

    // Execute
    const result = await listDecoderManifests();

    // Verify
    expect(result).toEqual({ decoderManifests: [] });
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
  });
});
