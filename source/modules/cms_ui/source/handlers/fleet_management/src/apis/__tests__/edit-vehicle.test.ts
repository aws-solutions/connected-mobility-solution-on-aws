// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { editVehicle } from "../edit-vehicle";
import {
  VehicleNotFound,
  VehicleBeingModified,
} from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  UpdateVehicleCommand,
  TagResourceCommand,
  ResourceNotFoundException,
  ConflictException,
} from "@aws-sdk/client-iotfleetwise";

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise");

describe("editVehicle", () => {
  const mockSend = jest.fn();
  const mockIoTFleetWiseClient = IoTFleetWiseClient as jest.MockedClass<
    typeof IoTFleetWiseClient
  >;

  beforeEach(() => {
    jest.clearAllMocks();
    mockIoTFleetWiseClient.prototype.send = mockSend;
  });

  it("should successfully edit a vehicle", async () => {
    // Arrange
    const input = {
      name: "test-vehicle",
      entry: {
        name: "test-vehicle",
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2023,
        licensePlate: "ABC123",
        tags: [
          { Key: "Tag1", Value: "Value1" },
          { Key: "Tag2", Value: "Value2" },
        ],
      },
    };

    const updateVehicleResponse = {
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/test-vehicle",
    };

    mockSend.mockResolvedValueOnce(updateVehicleResponse); // UpdateVehicleCommand response
    mockSend.mockResolvedValueOnce({}); // TagResourceCommand response

    // Act
    const result = await editVehicle(input);

    // Assert
    expect(mockSend).toHaveBeenCalledTimes(2);
    expect(mockIoTFleetWiseClient).toHaveBeenCalledTimes(1);

    expect(UpdateVehicleCommand).toHaveBeenCalledWith({
      vehicleName: input.name,
      attributes: {
        vin: input.entry.vin,
        make: input.entry.make,
        model: input.entry.model,
        year: "2023",
        license: input.entry.licensePlate,
      },
    });

    expect(TagResourceCommand).toHaveBeenCalledWith({
      ResourceARN: updateVehicleResponse.arn,
      Tags: input.entry.tags,
    });

    expect(result).toBeUndefined();
  });

  it("should not call TagResourceCommand if tags are undefined", async () => {
    // Arrange
    const input = {
      name: "test-vehicle",
      entry: {
        name: "test-vehicle",
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2023,
        licensePlate: "ABC123",
      },
    };

    const updateVehicleResponse = {
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/test-vehicle",
    };

    mockSend.mockResolvedValueOnce(updateVehicleResponse);

    // Act
    await editVehicle(input);

    // Assert
    expect(mockSend).toHaveBeenCalledTimes(1);
    expect(TagResourceCommand).not.toHaveBeenCalled();
  });

  it("should throw VehicleNotFound when vehicle doesn't exist during update", async () => {
    // Arrange
    const input = {
      name: "non-existent-vehicle",
      entry: {
        name: "non-existent-vehicle",
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2023,
        licensePlate: "ABC123",
      },
    };

    const error = new ResourceNotFoundException({
      message: "Resource not found",
      $metadata: {},
      resourceId: "non-existent-vehicle",
      resourceType: "vehicle",
    });
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editVehicle(input)).rejects.toThrow(VehicleNotFound);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should throw VehicleBeingModified when there's a conflict during update", async () => {
    // Arrange
    const input = {
      name: "busy-vehicle",
      entry: {
        name: "busy-vehicle",
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2023,
        licensePlate: "ABC123",
      },
    };

    const error = new ConflictException({
      message: "Conflict exception",
      $metadata: {},
      resourceType: "vehicle",
      resource: "busy-vehicle",
    });
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editVehicle(input)).rejects.toThrow(VehicleBeingModified);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should throw VehicleNotFound when vehicle doesn't exist during tag update", async () => {
    // Arrange
    const input = {
      name: "test-vehicle",
      entry: {
        name: "test-vehicle",
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2023,
        licensePlate: "ABC123",
        tags: [{ Key: "Tag1", Value: "Value1" }],
      },
    };

    const updateVehicleResponse = {
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/test-vehicle",
    };

    const error = new ResourceNotFoundException({
      message: "Resource not found",
      $metadata: {},
      resourceId: "test-vehicle",
      resourceType: "vehicle",
    });

    mockSend.mockResolvedValueOnce(updateVehicleResponse);
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editVehicle(input)).rejects.toThrow(VehicleNotFound);
    expect(mockSend).toHaveBeenCalledTimes(2);
  });

  it("should throw VehicleBeingModified when there's a conflict during tag update", async () => {
    // Arrange
    const input = {
      name: "test-vehicle",
      entry: {
        name: "test-vehicle",
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2023,
        licensePlate: "ABC123",
        tags: [{ Key: "Tag1", Value: "Value1" }],
      },
    };

    const updateVehicleResponse = {
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/test-vehicle",
    };

    const error = new ConflictException({
      message: "Conflict exception",
      $metadata: {},
      resourceType: "vehicle",
      resource: "test-vehicle",
    });

    mockSend.mockResolvedValueOnce(updateVehicleResponse);
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editVehicle(input)).rejects.toThrow(VehicleBeingModified);
    expect(mockSend).toHaveBeenCalledTimes(2);
  });

  it("should propagate other errors during vehicle update", async () => {
    // Arrange
    const input = {
      name: "test-vehicle",
      entry: {
        name: "test-vehicle",
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2023,
        licensePlate: "ABC123",
      },
    };

    const error = new Error("Some other error");
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editVehicle(input)).rejects.toThrow("Some other error");
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors during tag update", async () => {
    // Arrange
    const input = {
      name: "test-vehicle",
      entry: {
        name: "test-vehicle",
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2023,
        licensePlate: "ABC123",
        tags: [{ Key: "Tag1", Value: "Value1" }],
      },
    };

    const updateVehicleResponse = {
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/test-vehicle",
    };

    const error = new Error("Some other error");

    mockSend.mockResolvedValueOnce(updateVehicleResponse);
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editVehicle(input)).rejects.toThrow("Some other error");
    expect(mockSend).toHaveBeenCalledTimes(2);
  });
});
