// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SimulationCreate from "../../views/SimulationCreate";
import { IDeviceType, simTypes } from "../../components/Shared/Interfaces";
import { API } from "@aws-amplify/api";
import { I18n } from "@aws-amplify/core";

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  Link: jest.fn(),
  useNavigate: () => jest.fn(),
  useLocation: () => ({
    pathname: "localhost:3000/",
  }),
}));

beforeAll(() => {
  const mockDeviceTypes: IDeviceType[] = [
    {
      name: "custom-type-test",
      topic: "test",
      type_id: "test",
      payload: [
        {
          name: "test",
          type: "id",
        },
      ],
    },
    {
      name: "vehicle-demo-type-test",
      topic: "test",
      type_id: "test",
      payload: [
        {
          name: "test",
          type: "id",
        },
      ],
    },
  ];

  const mockAPI = {
    get: async () => mockDeviceTypes,
    post: jest.fn(),
  };
  jest.mock("@aws-amplify/api");
  API.get = mockAPI.get;
  API.post = mockAPI.post;
});

beforeEach(() => {
  render(<SimulationCreate region="us-east-1" title="test" />);
});

afterEach(() => {
  cleanup();
});

describe("SimulationCreate", () => {
  it("should render", async () => {
    await waitFor(() =>
      expect(
        screen.getByText(I18n.get("create.simulation"))
      ).toBeInTheDocument()
    );
  });

  it("should should show error for duplicate devices types", async () => {
    // getByRole suddenly stopped working for the select options here
    // Using document.getElementsByName instead
    await userEvent.selectOptions(
      await waitFor(() => document.getElementsByName("type_id")[0]),
      "test"
    );
    await userEvent.click(screen.getByRole("button", { name: "add.type" }));
    await userEvent.selectOptions(
      await waitFor(() => document.getElementsByName("type_id")[1]),
      "test"
    );
    expect(
      await screen.findByText(I18n.get("duplicate.device.error"))
    ).toBeInTheDocument();
  });

  it("should delete device type when delete button is clicked", async () => {
    await userEvent.click(screen.getByRole("button", { name: "add.type" }));
    expect(document.getElementsByName("type_id")).toHaveLength(2);
    await userEvent.click(screen.getAllByRole("button", { name: "delete" })[1]);
    expect(document.getElementsByName("type_id")).toHaveLength(1);
  });

  it("should successfully create simulation when submit button is clicked", async () => {
    await userEvent.type(screen.getByLabelText("simulation.name"), "test");
    await userEvent.selectOptions(
      screen.getByLabelText("device.type.select"),
      "test"
    );
    await userEvent.type(screen.getByLabelText("duration"), "5");
    await userEvent.click(screen.getByRole("button", { name: "save" }));
    await waitFor(() => expect(API.post).toBeCalled());
  });

  it("should render correct devices when the type is changed", async () => {
    waitFor(() =>
      expect(screen.getByText("custom-type-test")).toBeInTheDocument()
    );
    await userEvent.selectOptions(
      screen.getByLabelText("simulation.type"),
      simTypes.autoDemo
    );
    waitFor(() =>
      expect(screen.getByText("vehicle-demo-type-test")).toBeInTheDocument()
    );
  });
});
