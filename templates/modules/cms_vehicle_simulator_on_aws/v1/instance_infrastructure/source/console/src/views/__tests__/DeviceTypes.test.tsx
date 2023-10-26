// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, cleanup, waitFor } from "@testing-library/react";
import DeviceTypes from "../../views/DeviceTypes";
import userEvent from "@testing-library/user-event";
import { IDeviceType } from "../../components/Shared/Interfaces";
import { API } from "@aws-amplify/api";
import { I18n } from "@aws-amplify/core";

const mockDeviceType: IDeviceType[] = [
  {
    name: "test",
    topic: "test",
    type_id: "test",
    payload: [
      {
        name: "id-test",
        type: "id",
      },
    ],
  },
];

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  Link: () => {},
  useLocation: () => ({
    pathname: "localhost:3000/device/type",
  }),
}));

const mockAPI = {
  get: async () => mockDeviceType,
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
    expect(
      await waitFor(() => screen.getByText(I18n.get("device.types")))
    ).toBeInTheDocument();
  });

  it("should be removed when delete button is clicked", async () => {
    await waitFor(() => expect(screen.getAllByRole("row")).toHaveLength(2));
    await userEvent.click(screen.getByRole("button", { name: "delete" }));
    await userEvent.click(screen.getByRole("button", { name: "confirm" }));
    await waitFor(() => expect(screen.getAllByRole("row")).toHaveLength(1));
  });
});
