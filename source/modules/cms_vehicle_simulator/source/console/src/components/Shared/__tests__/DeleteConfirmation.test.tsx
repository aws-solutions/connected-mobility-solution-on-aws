// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, cleanup } from "@testing-library/react";
import DeleteConfirm from "../../../components/Shared/DeleteConfirmation";
import userEvent from "@testing-library/user-event";
import { I18n } from "@aws-amplify/core";

const mockDeleteFunction = jest.fn();
const mockShowFunction = jest.fn();

beforeEach(() => {
  render(
    <DeleteConfirm
      delete={mockDeleteFunction}
      id="test"
      index={1}
      name="test"
      show={true}
      showModal={mockShowFunction}
    />,
  );
});

afterEach(() => {
  cleanup();
});

describe("DeleteConfirmation", () => {
  it("should render", async () => {
    expect(
      screen.getByText(I18n.get("confirm.delete.title")),
    ).toBeInTheDocument();
  });

  it("should close modal", async () => {
    await userEvent.click(screen.getByRole("button", { name: "cancel" }));
    expect(mockShowFunction).toBeCalled();
  });

  it("should call delete and close modal", async () => {
    await userEvent.click(screen.getByRole("button", { name: "confirm" }));
    expect(mockDeleteFunction).toBeCalled();
    expect(mockShowFunction).toBeCalled();
  });
});
