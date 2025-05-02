// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, cleanup, waitFor } from "@testing-library/react";
import DeviceTypes from "../../views/DeviceTypes";
import userEvent from "@testing-library/user-event";
import { IDeviceType } from "../../components/Shared/Interfaces";
import { API } from "@aws-amplify/api";

const mockDeviceTypes: IDeviceType[] = [
  {
    name: "device-type-1",
    topic: "topic-1",
    type_id: "type-id-1",
    payload: [
      {
        name: "id-test-1",
        type: "id",
      },
    ],
  },
  {
    name: "device-type-2",
    topic: "topic-2",
    type_id: "type-id-2",
    payload: [
      {
        name: "id-test-2",
        type: "id",
      },
    ],
  }
];

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  Link: () => { },
  useLocation: () => ({
    pathname: "localhost:3000/device/type",
  }),
}));

const mockAPI = {
  get: async () => mockDeviceTypes,
  del: jest.fn(),
};
jest.mock("@aws-amplify/api");
API.get = mockAPI.get;
API.del = mockAPI.del;

beforeEach(() => {
  render(<DeviceTypes region="us-east-1" title="test" />);
});

afterEach(() => {
  cleanup();
});

describe("DeviceType", () => {
  it("should render", async () => {
    expect(await screen.findByText("device.types")).toBeInTheDocument();
  });

  it("should display all device types", async () => {
    expect(await screen.findByText("device-type-1")).toBeInTheDocument();
    expect(await screen.findByText("device-type-2")).toBeInTheDocument();
  });

  it("should delete the correct device type when delete button is clicked", async () => {
    await waitFor(() => expect(screen.getAllByRole("row")).toHaveLength(3)); // header + 2 rows

    // Get all delete buttons
    const deleteButtons = screen.getAllByRole("button", { name: "delete" });
    expect(deleteButtons).toHaveLength(2);

    // Click the first delete button
    await userEvent.click(deleteButtons[0]);

    // Confirm deletion
    await userEvent.click(screen.getByRole("button", { name: "confirm" }));

    // Verify the API was called with the correct ID
    expect(API.del).toHaveBeenCalledWith(expect.anything(), "/device/type/type-id-1", expect.anything());

    // Verify the first device type was removed from the list
    expect(await screen.findByText("device-type-2")).toBeInTheDocument();
    expect(screen.queryByText("device-type-1")).not.toBeInTheDocument();
  });

  it("should delete the second device type when its delete button is clicked", async () => {
    await waitFor(() => expect(screen.getAllByRole("row")).toHaveLength(3)); // header + 2 rows

    // Get all delete buttons
    const deleteButtons = screen.getAllByRole("button", { name: "delete" });

    // Click the second delete button
    await userEvent.click(deleteButtons[1]);

    // Confirm deletion
    await userEvent.click(screen.getByRole("button", { name: "confirm" }));

    // Verify the API was called with the correct ID
    expect(API.del).toHaveBeenCalledWith(expect.anything(), "/device/type/type-id-2", expect.anything());

    // Verify the second device type was removed from the list
    expect(await screen.findByText("device-type-1")).toBeInTheDocument();
    expect(screen.queryByText("device-type-2")).not.toBeInTheDocument();
  });
});
