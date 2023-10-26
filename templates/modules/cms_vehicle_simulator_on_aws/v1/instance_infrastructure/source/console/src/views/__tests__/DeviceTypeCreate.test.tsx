// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, cleanup, waitFor } from "@testing-library/react";
import DeviceTypeCreate from "../DeviceTypeCreate";
import { IDeviceType } from "../../components/Shared/Interfaces";
import userEvent from "@testing-library/user-event";
import { API } from "@aws-amplify/api";
import { I18n } from "@aws-amplify/core";

const mockVehicleDemoDeviceType: IDeviceType = {
  name: "vehicle-demo-test",
  topic: "test",
  type_id: "test",
  payload: [
    {
      name: "id-test",
      type: "id",
    },
    {
      name: "string-test",
      type: "string",
      min: 10,
      max: 10,
    },
    {
      name: "int-test",
      type: "int",
      min: 0,
      max: 10,
    },
    {
      name: "timestamp-test",
      type: "timestamp",
    },
    {
      name: "float-test",
      type: "float",
      min: 0,
      max: 10,
      precision: 2,
    },
    {
      name: "bool-test",
      type: "bool",
    },
    {
      name: "location-test",
      type: "location",
      long: 0,
      lat: 0,
      radius: 1,
    },
    {
      name: "pickone-test",
      type: "pickOne",
      arr: ["item-1", "item-2", "item-3"],
    },
    {
      name: "object-test",
      type: "object",
      payload: [
        {
          name: "nested-test",
          type: "id",
        },
      ],
    },
  ],
};

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  useNavigate: () => jest.fn(),
  useLocation: () => ({
    pathname: "localhost:3000/device/type/create",
  }),
}));

const mockAPI = {
  get: async () => mockVehicleDemoDeviceType,
  post: jest.fn(),
};
jest.mock("@aws-amplify/api");
API.get = mockAPI.get;
API.post = mockAPI.post;

beforeEach(() => {
  const deviceType: IDeviceType = {
    name: "test",
    topic: "test",
    type_id: "test",
    payload: [
      {
        name: "test",
        type: "id",
      },
    ],
  };

  render(
    <DeviceTypeCreate deviceType={deviceType} region="us-east-1" title="test" />
  );
});

afterEach(() => {
  cleanup();
});

describe("DeviceTypeCreate", () => {
  it("should render", async () => {
    await waitFor(() =>
      expect(
        screen.getByText(I18n.get("device.type.definition"))
      ).toBeInTheDocument()
    );
  });

  it("should render attribute when added", async () => {
    await userEvent.click(
      screen.getByRole("button", { name: "add.attribute" })
    );
    await userEvent.type(
      screen.getByRole("textbox", { name: "attribute-name" }),
      "test"
    );
    await userEvent.click(screen.getByRole("button", { name: "submit" }));
    expect(screen.getByText(/"test":/i)).toBeInTheDocument();
  });

  it("should render attribute modal when view button is clicked", async () => {
    await userEvent.click(
      screen.getByRole("button", { name: "add.attribute" })
    );
    await userEvent.type(
      screen.getByRole("textbox", { name: "attribute-name" }),
      "test"
    );
    await userEvent.click(screen.getByRole("button", { name: "submit" }));
    await userEvent.click(screen.getByRole("button", { name: "view" }));
    expect(screen.getByText(/"name": "test"/i)).toBeInTheDocument();
  });

  it("should remove attribute when delete button is clicked", async () => {
    await userEvent.click(
      screen.getByRole("button", { name: "add.attribute" })
    );
    await userEvent.type(
      screen.getByRole("textbox", { name: "attribute-name" }),
      "test"
    );
    await userEvent.click(screen.getByRole("button", { name: "submit" }));
    await userEvent.click(screen.getByRole("button", { name: "delete" }));
    expect(screen.getAllByRole("row")).toHaveLength(1);
  });

  it("should load attributes for vss when automotive demo button is clicked", async () => {
    await userEvent.click(screen.getByRole("button", { name: "vehicle.demo" }));
    expect(screen.getByText("id-test")).toBeInTheDocument;
  });

  it("should successfully post to device/type api on submit", async () => {
    await userEvent.click(screen.getByRole("button", { name: "vehicle.demo" }));
    await userEvent.click(screen.getByRole("button", { name: "save" }));
    await waitFor(() => expect(mockAPI.post).toBeCalled());
  });

  it("should render sample data", async () => {
    await userEvent.click(screen.getByRole("button", { name: "vehicle.demo" }));
    expect(screen.getByText(/asdqwiei1238/i)).toBeInTheDocument();
    expect(screen.getByText(/rLdMw4VRZ/i)).toBeInTheDocument();
    expect(screen.getByText(/10/i)).toBeInTheDocument();
    expect(
      screen.getByText(/[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/10/i)).toBeInTheDocument();
    expect(screen.getByText(/true/i)).toBeInTheDocument();
    expect(
      screen.getByText(/{ 'latitude': 0, 'longitude': 0 }/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/item-1/i)).toBeInTheDocument();
    expect(screen.getByText(/nested-test": "rLdMw4VRZ"/i)).toBeInTheDocument();
  });

  it("should export to json", async () => {
    const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, "click");

    await userEvent.click(screen.getByRole("button", { name: "vehicle.demo" }));
    await userEvent.click(screen.getByRole("button", { name: "export" }));
    expect(clickSpy).toBeCalled();
  });
});
