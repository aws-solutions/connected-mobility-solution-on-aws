// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ModalForm from "../ModalForm";
import { I18n } from "@aws-amplify/core";

const mockCloseModal = jest.fn();
const mockHandleModalSubmit = jest.fn();

beforeEach(() => {
  render(
    <ModalForm
      closeModal={mockCloseModal}
      handleModalSubmit={mockHandleModalSubmit}
      showModal={true}
    />,
  );
});

afterEach(() => {
  cleanup();
});

describe("ModalForm", () => {
  it("should render", () => {
    expect(screen.getByText(I18n.get("attribute.name"))).toBeInTheDocument();
  });

  it("should submit with valid data", async () => {
    await userEvent.type(
      screen.getByRole("textbox", { name: "attribute-name" }),
      "test",
    );
    await userEvent.click(screen.getByRole("button", { name: "submit" }));
    expect(mockCloseModal).toBeCalled();
    expect(mockHandleModalSubmit).toBeCalled();
  });

  it("should update attribute field defaults", async () => {
    await userEvent.selectOptions(document.getElementById("type")!, "object");
    await userEvent.selectOptions(document.getElementById("type")!, "id");
    expect(screen.getByText(/False/i)).toBeInTheDocument();
  });
});
