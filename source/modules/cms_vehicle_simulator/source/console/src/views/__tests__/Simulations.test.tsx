// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { API } from "@aws-amplify/api";
import userEvent from "@testing-library/user-event";
import Simulations from "../../views/Simulations";
import { ISimulation, simTypes } from "../../components/Shared/Interfaces";
import { I18n } from "@aws-amplify/core";

const mockSimulations: ISimulation[] = [
  {
    name: "test",
    stage: "sleeping",
    sim_id: "test",
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

const mockAPI = {
  get: async () => mockSimulations,
  post: jest.fn(),
  del: jest.fn(),
};
jest.mock("@aws-amplify/api");
API.get = mockAPI.get;
API.post = mockAPI.post;
API.del = mockAPI.del;

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  Link: jest.fn(),
  useLocation: () => ({
    pathname: "localhost:3000/",
  }),
}));

beforeEach(() => {
  render(<Simulations region="us-east-1" title="test" />);
});

afterEach(() => {
  cleanup();
});

describe("Simulations", () => {
  it("should render", async () => {
    expect(
      await waitFor(() => screen.getByText(`${I18n.get("simulations")} (0)`)),
    ).toBeInTheDocument();
  });

  it("should handle checkbox select all", async () => {
    await userEvent.click(
      await waitFor(() => screen.getByRole("checkbox", { name: "all" })),
    );

    const checkboxes = await waitFor(() => screen.getAllByRole("checkbox"));

    checkboxes.forEach((checkbox) => {
      expect(checkbox).toBeChecked();
    });

    await userEvent.click(screen.getByRole("checkbox", { name: "all" }));

    checkboxes.forEach((checkbox) => {
      expect(checkbox).not.toBeChecked();
    });
  });

  it("should render buttons when one or more checkboxes are selected", async () => {
    await waitFor(() => screen.getByText(I18n.get("delete")));
    await userEvent.click(screen.getAllByRole("checkbox")[1]);
    await waitFor(() =>
      expect(
        screen.getByText(I18n.get("simulation.start")),
      ).toBeInTheDocument(),
    );
  });

  it("should start all selected simulations", async () => {
    await userEvent.click(screen.getByRole("checkbox", { name: "all" }));
    await userEvent.click(screen.getByText(I18n.get("simulation.start")));
    await waitFor(() =>
      expect(screen.getAllByRole("row")).toHaveLength(
        mockSimulations.length + 1,
      ),
    );
  });

  it("should start all selected simulations", async () => {
    await userEvent.click(screen.getByRole("checkbox", { name: "all" }));
    await userEvent.click(screen.getByText(I18n.get("simulation.start")));
    await waitFor(() =>
      expect(screen.getAllByText("running")).toHaveLength(
        mockSimulations.length,
      ),
    );
    await userEvent.click(screen.getByText(I18n.get("simulation.stop")));
    await waitFor(() =>
      expect(screen.getAllByText("stopping")).toHaveLength(
        mockSimulations.length,
      ),
    );
  });

  it("should remove simulations when deleted", async () => {
    await waitFor(() => screen.getByText("test"));
    expect(screen.getAllByRole("row")).toHaveLength(2);
    await userEvent.click(screen.getByRole("button", { name: "delete" }));
    await userEvent.click(screen.getByRole("button", { name: "confirm" }));
    expect(screen.getAllByRole("row")).toHaveLength(1);
  });

  it("should show info modal when info button is clicked", async () => {
    await waitFor(() => screen.getByText("test"));
    await userEvent.click(screen.getByRole("button", { name: "info" }));
    expect(screen.getByText(I18n.get("device.types"))).toBeInTheDocument();
    expect(screen.getByText(I18n.get("amount"))).toBeInTheDocument();
  });
});
