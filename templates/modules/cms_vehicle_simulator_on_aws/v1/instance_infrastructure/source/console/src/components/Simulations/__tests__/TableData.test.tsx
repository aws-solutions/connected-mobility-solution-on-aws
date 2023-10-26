// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen } from "@testing-library/react";
import TableData from "../TableData";
import { ISimulation, simTypes } from "../../Shared/Interfaces";
import Table from "react-bootstrap/Table";

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  Link: () => {},
}));

const mockSimulations: ISimulation[] = [
  {
    sim_id: "test",
    name: "test",
    stage: "sleeping",
    interval: 1,
    duration: 10,
    devices: [
      {
        name: "test",
        type_id: simTypes.custom,
        amount: 1,
      },
    ],
  },
];

describe("TableData", () => {
  it("should render", () => {
    render(
      <Table>
        <TableData
          handleCheckboxSelect={() => {}}
          setSimulations={() => {}}
          simulations={mockSimulations}
        />
      </Table>
    );
    expect(screen.getByText("test")).toBeInTheDocument();
  });
});
