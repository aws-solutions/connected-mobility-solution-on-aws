// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { editFleet } from "../edit-fleet";
import {
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

// Mock the AWS SDK
jest.mock("@aws-sdk/client-iotfleetwise");

describe("editFleet", () => {
  const mockSend = jest.fn();
  const mockIoTFleetWiseClient = IoTFleetWiseClient as jest.MockedClass<
    typeof IoTFleetWiseClient
  >;

  beforeEach(() => {
    jest.clearAllMocks();
    mockIoTFleetWiseClient.prototype.send = mockSend;
  });

  it("should successfully edit a fleet", async () => {
    // Arrange
    const input = {
      id: "test-fleet",
      entry: {
        id: "test-fleet",
        name: "Updated Fleet Name",
        description: "Updated fleet description",
        tags: [
          { Key: "Tag1", Value: "Value1" },
          { Key: "Tag2", Value: "Value2" },
        ],
      },
    };

    const updateFleetResponse = {
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/test-fleet",
    };

    mockSend.mockResolvedValueOnce(updateFleetResponse); // UpdateFleetCommand response
    mockSend.mockResolvedValueOnce({}); // TagResourceCommand response

    // Act
    const result = await editFleet(input);

    // Assert
    expect(mockSend).toHaveBeenCalledTimes(2);
    expect(mockIoTFleetWiseClient).toHaveBeenCalledTimes(1);

    expect(UpdateFleetCommand).toHaveBeenCalledWith({
      fleetId: input.id,
      description: input.entry.description,
    });

    expect(TagResourceCommand).toHaveBeenCalledWith({
      ResourceARN: updateFleetResponse.arn,
      Tags: [
        { Key: "DisplayName", Value: input.entry.name },
        { Key: "Tag1", Value: "Value1" },
        { Key: "Tag2", Value: "Value2" },
      ],
    });

    expect(result).toBeUndefined();
  });

  it("should handle empty description by setting it to undefined", async () => {
    // Arrange
    const input = {
      id: "test-fleet",
      entry: {
        id: "test-fleet",
        name: "Updated Fleet Name",
        description: "",
        tags: [{ Key: "Tag1", Value: "Value1" }],
      },
    };

    const updateFleetResponse = {
      arn: "arn:aws:iotfleetwise:us-east-1:123456789012:fleet/test-fleet",
    };

    mockSend.mockResolvedValueOnce(updateFleetResponse);
    mockSend.mockResolvedValueOnce({});

    // Act
    await editFleet(input);

    // Assert
    expect(UpdateFleetCommand).toHaveBeenCalledWith({
      fleetId: input.id,
      description: undefined,
    });
  });

  it("should throw FleetNotFound when fleet doesn't exist", async () => {
    // Arrange
    const input = {
      id: "non-existent-fleet",
      entry: {
        id: "non-existent-fleet",
        name: "Updated Fleet Name",
        description: "Updated fleet description",
        tags: [],
      },
    };

    const error = new ResourceNotFoundException({
      message: "Resource not found",
      $metadata: {},
      resourceId: "non-existent-fleet",
      resourceType: "fleet",
    });
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editFleet(input)).rejects.toThrow(FleetNotFound);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should throw FleetBeingModified when there's a conflict", async () => {
    // Arrange
    const input = {
      id: "busy-fleet",
      entry: {
        id: "busy-fleet",
        name: "Updated Fleet Name",
        description: "Updated fleet description",
        tags: [],
      },
    };

    const error = new ConflictException({
      message: "Conflict exception",
      $metadata: {},
      resourceType: "fleet",
      resource: "busy-fleet",
    });
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editFleet(input)).rejects.toThrow(FleetBeingModified);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors", async () => {
    // Arrange
    const input = {
      id: "test-fleet",
      entry: {
        id: "test-fleet",
        name: "Updated Fleet Name",
        description: "Updated fleet description",
        tags: [],
      },
    };

    const error = new Error("Some other error");
    mockSend.mockRejectedValueOnce(error);

    // Act & Assert
    await expect(editFleet(input)).rejects.toThrow("Some other error");
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
