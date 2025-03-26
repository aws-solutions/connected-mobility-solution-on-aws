// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { VehicleStatus } from "@com.cms.fleetmanagement/api-server";
import { IoTFleetWiseClient } from "@aws-sdk/client-iotfleetwise";
import { listVehicles } from "../list-vehicles";
import { getVehicleStatus } from "../utils";

// Mock the AWS SDK clients
jest.mock("@aws-sdk/client-iotfleetwise");
jest.mock("../utils");

describe("listVehicles", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should return a list of vehicles with their details", async () => {
    // Mock data
    const mockVehicleSummaries = [
      {
        vehicleName: "vehicle-1",
        attributes: {
          vin: "VIN123456789",
          make: "Toyota",
          model: "Camry",
          year: "2020",
          license: "ABC123",
        },
      },
      {
        vehicleName: "vehicle-2",
        attributes: {
          vin: "VIN987654321",
          make: "Honda",
          model: "Civic",
          year: "2021",
          license: "XYZ789",
        },
      },
    ];

    // Setup mocks
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      vehicleSummaries: mockVehicleSummaries,
    });

    (getVehicleStatus as jest.Mock).mockImplementation((vehicleName) => {
      if (vehicleName === "vehicle-1") {
        return Promise.resolve(VehicleStatus.ACTIVE);
      } else {
        return Promise.resolve(VehicleStatus.INACTIVE);
      }
    });

    // Execute
    const result = await listVehicles();

    // Verify
    expect(result).toEqual({
      vehicles: [
        {
          name: "vehicle-1",
          status: VehicleStatus.ACTIVE,
          attributes: {
            vin: "VIN123456789",
            make: "Toyota",
            model: "Camry",
            year: 2020,
            licensePlate: "ABC123",
          },
        },
        {
          name: "vehicle-2",
          status: VehicleStatus.INACTIVE,
          attributes: {
            vin: "VIN987654321",
            make: "Honda",
            model: "Civic",
            year: 2021,
            licensePlate: "XYZ789",
          },
        },
      ],
    });

    // Verify calls
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
    expect(getVehicleStatus).toHaveBeenCalledWith("vehicle-1");
    expect(getVehicleStatus).toHaveBeenCalledWith("vehicle-2");
  });

  it("should handle empty vehicle list", async () => {
    // Mock empty response
    IoTFleetWiseClient.prototype.send = jest.fn().mockResolvedValue({
      vehicleSummaries: [],
    });

    // Execute
    const result = await listVehicles();

    // Verify
    expect(result).toEqual({ vehicles: [] });
    expect(IoTFleetWiseClient.prototype.send).toHaveBeenCalledTimes(1);
    expect(getVehicleStatus).not.toHaveBeenCalled();
  });
});
