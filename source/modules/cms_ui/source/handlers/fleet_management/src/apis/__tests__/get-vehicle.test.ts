// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { VehicleNotFound } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { getVehicle } from "../get-vehicle";
import { getVehicleStatus } from "../utils";

// Mock the AWS SDK clients and commands
jest.mock("@aws-sdk/client-iotfleetwise");
jest.mock("../utils");

describe("getVehicle", () => {
  const mockSend = jest.fn();
  const mockGetVehicleStatus = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));
    (getVehicleStatus as jest.Mock).mockImplementation(mockGetVehicleStatus);
  });

  it("should return vehicle details when vehicle exists", async () => {
    // Mock responses
    const vehicleName = "test-vehicle";
    const vehicleArn =
      "arn:aws:iotfleetwise:us-east-1:123456789012:vehicle/test-vehicle";

    mockSend.mockImplementation((command) => {
      if (command.constructor.name === "GetVehicleCommand") {
        return {
          vehicleName,
          arn: vehicleArn,
          attributes: {
            vin: "1HGCM82633A123456",
            make: "Toyota",
            model: "Camry",
            year: "2022",
            license: "ABC123",
          },
        };
      } else if (command.constructor.name === "ListTagsForResourceCommand") {
        return {
          Tags: [
            { Key: "Environment", Value: "Production" },
            { Key: "Owner", Value: "Fleet Team" },
          ],
        };
      }
    });

    mockGetVehicleStatus.mockResolvedValue("ACTIVE");

    // Execute
    const result = await getVehicle({ name: vehicleName });

    // Verify
    expect(result).toEqual({
      name: vehicleName,
      status: "ACTIVE",
      attributes: {
        vin: "1HGCM82633A123456",
        make: "Toyota",
        model: "Camry",
        year: 2022,
        licensePlate: "ABC123",
      },
      tags: [
        { Key: "Environment", Value: "Production" },
        { Key: "Owner", Value: "Fleet Team" },
      ],
    });
    expect(mockSend).toHaveBeenCalledTimes(2);
    expect(mockGetVehicleStatus).toHaveBeenCalledWith(vehicleName);
  });

  it("should throw VehicleNotFound when vehicle does not exist", async () => {
    // Mock responses
    const vehicleName = "non-existent-vehicle";
    mockSend.mockImplementation(() => {
      throw new ResourceNotFoundException({
        message: "Resource not found",
        $metadata: {},
        resourceId: vehicleName,
        resourceType: "VEHICLE",
      });
    });

    // Execute and verify
    await expect(getVehicle({ name: vehicleName })).rejects.toThrow(
      VehicleNotFound,
    );
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors", async () => {
    // Mock responses
    const vehicleName = "error-vehicle";
    const error = new Error("Network error");
    mockSend.mockRejectedValue(error);

    // Execute and verify
    await expect(getVehicle({ name: vehicleName })).rejects.toThrow(
      "Network error",
    );
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
