// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CreateFleetInput } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  CreateFleetCommand,
} from "@aws-sdk/client-iotfleetwise";
import { createFleet } from "../create-fleet";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise", () => {
  const mockSend = jest.fn().mockResolvedValue({});
  const mockIoTFleetWiseClient = jest.fn(() => ({
    send: mockSend,
  }));
  return {
    IoTFleetWiseClient: mockIoTFleetWiseClient,
    CreateFleetCommand: jest.fn().mockImplementation((params) => params),
  };
});

describe("createFleet", () => {
  let mockClient: jest.Mocked<IoTFleetWiseClient>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockClient = new IoTFleetWiseClient() as jest.Mocked<IoTFleetWiseClient>;
  });

  it("should create a fleet with required parameters", async () => {
    // Arrange
    jest.clearAllMocks(); // Clear mock calls before this specific test
    const input: CreateFleetInput = {
      entry: {
        id: "fleet-123",
        name: "Test Fleet",
        signalCatalogArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
      },
    };

    // Act
    await createFleet(input);

    // Assert
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(CreateFleetCommand).toHaveBeenCalledWith({
      fleetId: "fleet-123",
      description: undefined,
      signalCatalogArn:
        "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
      tags: [{ Key: "DisplayName", Value: "Test Fleet" }],
    });
    expect(mockClient.send).toHaveBeenCalledTimes(1);
  });

  it("should create a fleet with description when provided", async () => {
    // Arrange
    const input: CreateFleetInput = {
      entry: {
        id: "fleet-123",
        name: "Test Fleet",
        description: "This is a test fleet",
        signalCatalogArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
      },
    };

    // Act
    await createFleet(input);

    // Assert
    expect(CreateFleetCommand).toHaveBeenCalledWith({
      fleetId: "fleet-123",
      description: "This is a test fleet",
      signalCatalogArn:
        "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
      tags: [{ Key: "DisplayName", Value: "Test Fleet" }],
    });
  });

  it("should set description to undefined when empty string is provided", async () => {
    // Arrange
    const input: CreateFleetInput = {
      entry: {
        id: "fleet-123",
        name: "Test Fleet",
        description: "",
        signalCatalogArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
      },
    };

    // Act
    await createFleet(input);

    // Assert
    expect(CreateFleetCommand).toHaveBeenCalledWith({
      fleetId: "fleet-123",
      description: undefined,
      signalCatalogArn:
        "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
      tags: [{ Key: "DisplayName", Value: "Test Fleet" }],
    });
  });

  it("should include additional tags when provided", async () => {
    // Arrange
    const input: CreateFleetInput = {
      entry: {
        id: "fleet-123",
        name: "Test Fleet",
        signalCatalogArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
        tags: [
          { Key: "Environment", Value: "Production" },
          { Key: "Owner", Value: "Team-A" },
        ],
      },
    };

    // Act
    await createFleet(input);

    // Assert
    expect(CreateFleetCommand).toHaveBeenCalledWith({
      fleetId: "fleet-123",
      description: undefined,
      signalCatalogArn:
        "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
      tags: [
        { Key: "DisplayName", Value: "Test Fleet" },
        { Key: "Environment", Value: "Production" },
        { Key: "Owner", Value: "Team-A" },
      ],
    });
  });

  it("should handle errors from the AWS SDK", async () => {
    // Arrange
    const mockError = new Error("AWS SDK Error");
    const mockSend = jest.fn().mockRejectedValueOnce(mockError);

    // Override the mock implementation for this test
    (IoTFleetWiseClient as jest.Mock).mockImplementationOnce(() => ({
      send: mockSend,
    }));

    const input: CreateFleetInput = {
      entry: {
        id: "fleet-123",
        name: "Test Fleet",
        signalCatalogArn:
          "arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test-catalog",
      },
    };

    // Act & Assert
    await expect(createFleet(input)).rejects.toThrow("AWS SDK Error");
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
