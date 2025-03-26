// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { createVehicle } from "../create-vehicle";
import {
  IoTFleetWiseClient,
  CreateVehicleCommand,
  GetDecoderManifestCommand,
  VehicleAssociationBehavior,
} from "@aws-sdk/client-iotfleetwise";
import { CreateVehicleInput } from "@com.cms.fleetmanagement/api-server";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise", () => {
  const originalModule = jest.requireActual("@aws-sdk/client-iotfleetwise");
  return {
    __esModule: true,
    ...originalModule,
    IoTFleetWiseClient: jest.fn(),
    CreateVehicleCommand: jest.fn(),
    GetDecoderManifestCommand: jest.fn(),
  };
});

describe("createVehicle", () => {
  // Setup mocks
  const mockSend = jest.fn();
  const mockIoTFleetWiseClient = {
    send: mockSend,
  };

  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();

    // Mock the IoTFleetWiseClient constructor
    (IoTFleetWiseClient as unknown as jest.Mock).mockImplementation(
      () => mockIoTFleetWiseClient,
    );

    // Mock the command constructors
    (GetDecoderManifestCommand as unknown as jest.Mock).mockImplementation(
      (params) => ({
        ...params,
        constructor: { name: "GetDecoderManifestCommand" },
      }),
    );

    (CreateVehicleCommand as unknown as jest.Mock).mockImplementation(
      (params) => ({
        ...params,
        constructor: { name: "CreateVehicleCommand" },
      }),
    );

    // Default mock response for getDecoderManifest
    mockSend.mockResolvedValueOnce({
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:decoder-manifest/test-decoder",
      modelManifestArn:
        "arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/test-model",
    });
  });

  it("should call GetDecoderManifestCommand with the correct parameters", async () => {
    // Arrange
    const input = {
      entry: {
        name: "test-vehicle",
        decoderManifestName: "test-decoder-manifest",
        vin: "1HGCM82633A123456",
        make: "Test Make",
        model: "Test Model",
        year: 2023,
        licensePlate: "ABC123",
      },
    } as CreateVehicleInput;

    // Act
    await createVehicle(input);

    // Assert
    expect(GetDecoderManifestCommand).toHaveBeenCalledWith({
      name: "test-decoder-manifest",
    });
  });

  it("should call CreateVehicleCommand with the correct parameters", async () => {
    // Arrange
    const input = {
      entry: {
        name: "test-vehicle",
        decoderManifestName: "test-decoder-manifest",
        vin: "1HGCM82633A123456",
        make: "Test Make",
        model: "Test Model",
        year: 2023,
        licensePlate: "ABC123",
      },
    } as CreateVehicleInput;

    // Act
    await createVehicle(input);

    // Assert
    expect(CreateVehicleCommand).toHaveBeenCalledWith({
      vehicleName: "test-vehicle",
      modelManifestArn:
        "arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/test-model",
      decoderManifestArn:
        "arn:aws:iotfleetwise:us-east-1:123456789012:decoder-manifest/test-decoder",
      associationBehavior: VehicleAssociationBehavior.CREATE_IOT_THING,
      attributes: {
        vin: "1HGCM82633A123456",
        make: "Test Make",
        model: "Test Model",
        year: "2023",
        license: "ABC123",
      },
      tags: [],
    });
  });

  it("should include tags when provided", async () => {
    // Arrange
    const input = {
      entry: {
        name: "test-vehicle",
        decoderManifestName: "test-decoder-manifest",
        vin: "1HGCM82633A123456",
        make: "Test Make",
        model: "Test Model",
        year: 2023,
        licensePlate: "ABC123",
        tags: [
          { Key: "Environment", Value: "Test" },
          { Key: "Project", Value: "CMS" },
        ],
      },
    } as CreateVehicleInput;

    // Act
    await createVehicle(input);

    // Assert
    expect(CreateVehicleCommand).toHaveBeenCalledWith(
      expect.objectContaining({
        tags: [
          { Key: "Environment", Value: "Test" },
          { Key: "Project", Value: "CMS" },
        ],
      }),
    );
  });

  it("should handle errors from IoTFleetWise client", async () => {
    // Arrange
    const input = {
      entry: {
        name: "test-vehicle",
        decoderManifestName: "test-decoder-manifest",
        vin: "1HGCM82633A123456",
        make: "Test Make",
        model: "Test Model",
        year: 2023,
        licensePlate: "ABC123",
      },
    } as CreateVehicleInput;

    // Mock GetDecoderManifestCommand to succeed but CreateVehicleCommand to fail
    mockSend.mockReset();
    mockSend.mockResolvedValueOnce({
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:decoder-manifest/test-decoder",
      modelManifestArn:
        "arn:aws:iotfleetwise:us-east-1:123456789012:model-manifest/test-model",
    });
    mockSend.mockRejectedValueOnce(new Error("Failed to create vehicle"));

    // Act & Assert
    await expect(createVehicle(input)).rejects.toThrow(
      "Failed to create vehicle",
    );
  });

  it("should handle errors from GetDecoderManifestCommand", async () => {
    // Arrange
    const input = {
      entry: {
        name: "test-vehicle",
        decoderManifestName: "test-decoder-manifest",
        vin: "1HGCM82633A123456",
        make: "Test Make",
        model: "Test Model",
        year: 2023,
        licensePlate: "ABC123",
      },
    } as CreateVehicleInput;

    // Mock GetDecoderManifestCommand to fail
    mockSend.mockReset();
    mockSend.mockRejectedValueOnce(new Error("Decoder manifest not found"));

    // Act & Assert
    await expect(createVehicle(input)).rejects.toThrow(
      "Decoder manifest not found",
    );
  });
});
