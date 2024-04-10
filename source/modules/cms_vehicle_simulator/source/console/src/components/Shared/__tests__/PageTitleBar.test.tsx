// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, waitFor } from "@testing-library/react";
import PageTitleBar from "../PageTitleBar";
import { API } from "@aws-amplify/api";

jest.mock("react-router-dom", () => ({
  ...(jest.requireActual("react-router-dom") as any),
  useLocation: () => ({
    pathname: "localhost:3000/",
  }),
}));

const mockAPI = {
  get: jest.fn(),
};
jest.mock("@aws-amplify/api");
API.get = mockAPI.get;

jest.useFakeTimers();

describe("PageTitleBar", () => {
  it("should render", async () => {
    render(<PageTitleBar title="PageTitleBar" />);
    jest.advanceTimersToNextTimer();
    expect(
      await waitFor(() => screen.getByText("PageTitleBar")),
    ).toBeInTheDocument();
  });
});
