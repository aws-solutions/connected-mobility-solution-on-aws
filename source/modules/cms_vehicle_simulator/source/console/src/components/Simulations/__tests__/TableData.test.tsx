// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, within } from "@testing-library/react";
import TableData from "../TableData";
import { ISimulation, simTypes } from "../../Shared/Interfaces";
import Table from "react-bootstrap/Table";
import userEvent from "@testing-library/user-event";
import { API } from "@aws-amplify/api";

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  Link: () => { },
}));

jest.mock("@aws-amplify/api");

const mockSimulations: ISimulation[] = [
  {
    sim_id: "sim-id-1",
    name: "simulation-1",
    stage: "sleeping",
    interval: 1,
    duration: 10,
    devices: [
      {
        name: "device-1",
        type_id: simTypes.custom,
        amount: 1,
      },
    ],
  },
  {
    sim_id: "sim-id-2",
    name: "simulation-2",
    stage: "running",
    interval: 2,
    duration: 20,
    devices: [
      {
        name: "device-2",
        type_id: simTypes.custom,
        amount: 2,
      },
    ],
  },
];

const mockSetSimulations = jest.fn();
const mockHandleCheckboxSelect = jest.fn();

describe("TableData", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    API.del = jest.fn().mockResolvedValue({});
  });

  it("should render all simulations", () => {
    render(
      <Table>
        <TableData
          handleCheckboxSelect={mockHandleCheckboxSelect}
          setSimulations={mockSetSimulations}
          simulations={mockSimulations}
        />
      </Table>,
    );

    expect(screen.getByText("simulation-1")).toBeInTheDocument();
    expect(screen.getByText("simulation-2")).toBeInTheDocument();
    expect(screen.getByText("sleeping")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
  });

  it("should delete the correct simulation when delete button is clicked", async () => {
    render(
      <Table>
        <TableData
          handleCheckboxSelect={mockHandleCheckboxSelect}
          setSimulations={mockSetSimulations}
          simulations={[...mockSimulations]}
        />
      </Table>,
    );

    // Get all delete buttons
    const deleteButtons = screen.getAllByRole("button", { name: "delete" });
    expect(deleteButtons).toHaveLength(2);

    // Click the first delete button
    await userEvent.click(deleteButtons[0]);

    // Confirm deletion
    await userEvent.click(screen.getByRole("button", { name: "confirm" }));

    // Verify the API was called with the correct ID
    expect(API.del).toHaveBeenCalledWith(expect.anything(), "/simulation/sim-id-1", expect.anything());

    // Verify setSimulations was called with updated simulations array
    expect(mockSetSimulations).toHaveBeenCalled();
    const updatedSimulations = mockSetSimulations.mock.calls[0][0];
    expect(updatedSimulations).toHaveLength(1);
    expect(updatedSimulations[0].sim_id).toBe("sim-id-2");
  });

  it("should delete the second simulation when its delete button is clicked", async () => {
    render(
      <Table>
        <TableData
          handleCheckboxSelect={mockHandleCheckboxSelect}
          setSimulations={mockSetSimulations}
          simulations={[...mockSimulations]}
        />
      </Table>,
    );

    // Get all delete buttons
    const deleteButtons = screen.getAllByRole("button", { name: "delete" });

    // Click the second delete button
    await userEvent.click(deleteButtons[1]);

    // Confirm deletion
    await userEvent.click(screen.getByRole("button", { name: "confirm" }));

    // Verify the API was called with the correct ID
    expect(API.del).toHaveBeenCalledWith(expect.anything(), "/simulation/sim-id-2", expect.anything());

    // Verify setSimulations was called with updated simulations array
    expect(mockSetSimulations).toHaveBeenCalled();
    const updatedSimulations = mockSetSimulations.mock.calls[0][0];
    expect(updatedSimulations).toHaveLength(1);
    expect(updatedSimulations[0].sim_id).toBe("sim-id-1");
  });

  it("should show device info modal when info button is clicked", async () => {
    render(
      <Table>
        <TableData
          handleCheckboxSelect={mockHandleCheckboxSelect}
          setSimulations={mockSetSimulations}
          simulations={mockSimulations}
        />
      </Table>,
    );

    // Get all info buttons
    const infoButtons = screen.getAllByRole("button", { name: "info" });
    expect(infoButtons).toHaveLength(2);

    // Click the first info button
    await userEvent.click(infoButtons[0]);

    // Verify the modal shows with correct simulation name
    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();

    // Verify the content within the modal
    const { getByText } = within(modal);
    expect(getByText("simulation-1")).toBeInTheDocument();
    expect(getByText("device-1")).toBeInTheDocument();
  });
});
