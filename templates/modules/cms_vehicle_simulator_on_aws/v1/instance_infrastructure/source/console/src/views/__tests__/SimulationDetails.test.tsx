// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, waitFor, cleanup } from "@testing-library/react";
import { ISimulation, simTypes } from "../../components/Shared/Interfaces";
import SimulationDetails from "../../views/SimulationDetails";
import userEvent from "@testing-library/user-event";
import { API } from "@aws-amplify/api";
import { I18n } from "@aws-amplify/core";

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  useLocation: () => ({
    pathname: "localhost:3000/simulations/test",
  }),
}));

const mockSimulation: ISimulation = {
  name: "test",
  sim_id: "test",
  devices: [
    {
      amount: 1,
      name: "test",
      type_id: simTypes.custom,
    },
  ],
  interval: 1,
  duration: 10,
  stage: "sleeping",
};

const mockAPI = {
  get: async () => mockSimulation,
  put: jest.fn(),
};
jest.mock("@aws-amplify/api");
API.get = mockAPI.get;
API.put = mockAPI.put;

beforeEach(() => {
  render(
    <SimulationDetails region="us-east-1" title="test" topicPrefix="test" />
  );
});

afterEach(() => {
  cleanup();
});

describe("SimulationDetails", () => {
  it("should render", async () => {
    await waitFor(() =>
      expect(screen.getByText(I18n.get("messages"))).toBeInTheDocument()
    );
  });

  it("should start when start button is clicked", async () => {
    await userEvent.click(screen.getByRole("button", { name: "start" }));
    await waitFor(() =>
      expect(screen.getByText("running")).toBeInTheDocument()
    );
    expect(mockAPI.put).toBeCalled();
  });

  it("should stop when stop button is clicked", async () => {
    await userEvent.click(screen.getByRole("button", { name: "start" }));
    await waitFor(() =>
      expect(screen.getByText("running")).toBeInTheDocument()
    );
    await userEvent.click(screen.getByRole("button", { name: "stop" }));
    await waitFor(() =>
      expect(screen.getByText("stopping")).toBeInTheDocument()
    );
    expect(mockAPI.put).toBeCalled();
  });
});
