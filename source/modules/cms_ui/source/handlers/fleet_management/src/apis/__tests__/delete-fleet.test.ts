// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { deleteFleet } from "../delete-fleet";
import { FleetNotFound } from "@com.cms.fleetmanagement/api-server";
import {
  IoTFleetWiseClient,
  DeleteFleetCommand,
  ResourceNotFoundException,
} from "@aws-sdk/client-iotfleetwise";
import { listCampaignsForTarget } from "../list-campaigns-for-target";
import { listVehiclesInFleet } from "../list-vehicles-in-fleet";
import { deleteCampaign } from "../delete-campaign";
import { disassociateVehicle } from "../disassociate-vehicle";

// Mock the AWS SDK and dependent functions
jest.mock("@aws-sdk/client-iotfleetwise");
jest.mock("../list-campaigns-for-target");
jest.mock("../list-vehicles-in-fleet");
jest.mock("../delete-campaign");
jest.mock("../disassociate-vehicle");

describe("deleteFleet", () => {
  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should delete a fleet successfully", async () => {
    // Setup mock implementations
    const mockSend = jest.fn().mockResolvedValue({});
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));

    // Mock dependent functions
    (listCampaignsForTarget as jest.Mock).mockResolvedValue({
      campaigns: [{ name: "campaign1" }, { name: "campaign2" }],
    });
    (listVehiclesInFleet as jest.Mock).mockResolvedValue({
      vehicles: [{ name: "vehicle1" }, { name: "vehicle2" }],
    });
    (deleteCampaign as jest.Mock).mockResolvedValue({});
    (disassociateVehicle as jest.Mock).mockResolvedValue({});

    // Call the function
    const result = await deleteFleet({ id: "test-fleet" });

    // Verify the results
    expect(result).toBeUndefined();
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledTimes(1);
    expect(DeleteFleetCommand).toHaveBeenCalledWith({
      fleetId: "test-fleet",
    });

    // Verify dependent functions were called
    expect(listCampaignsForTarget).toHaveBeenCalledTimes(1);
    expect(listVehiclesInFleet).toHaveBeenCalledTimes(1);
    expect(deleteCampaign).toHaveBeenCalledTimes(2); // Once for each campaign
    expect(disassociateVehicle).toHaveBeenCalledTimes(2); // Once for each vehicle
  });

  it("should throw FleetNotFound when fleet doesn't exist", async () => {
    // Setup mock implementations
    const mockSend = jest.fn().mockRejectedValue(
      new ResourceNotFoundException({
        message: "Resource not found",
        $metadata: {},
        resourceId: "non-existent-fleet",
        resourceType: "Fleet",
      }),
    );
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));

    // Mock dependent functions with empty results
    (listCampaignsForTarget as jest.Mock).mockResolvedValue({ campaigns: [] });
    (listVehiclesInFleet as jest.Mock).mockResolvedValue({ vehicles: [] });

    // Call the function and expect it to throw
    await expect(deleteFleet({ id: "non-existent-fleet" })).rejects.toThrow(
      FleetNotFound,
    );

    // Verify the mock was called
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });

  it("should propagate other errors", async () => {
    // Setup mock implementation to throw a different error
    const error = new Error("Some other error");
    const mockSend = jest.fn().mockRejectedValue(error);
    (IoTFleetWiseClient as jest.Mock).mockImplementation(() => ({
      send: mockSend,
    }));

    // Mock dependent functions with empty results
    (listCampaignsForTarget as jest.Mock).mockResolvedValue({ campaigns: [] });
    (listVehiclesInFleet as jest.Mock).mockResolvedValue({ vehicles: [] });

    // Call the function and expect it to throw the original error
    await expect(deleteFleet({ id: "test-fleet" })).rejects.toThrow(
      "Some other error",
    );

    // Verify the mock was called
    expect(IoTFleetWiseClient).toHaveBeenCalledTimes(1);
    expect(mockSend).toHaveBeenCalledTimes(1);
  });
});
