// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen, cleanup } from "@testing-library/react";
import Footer from "../../../components/Shared/Footer";
import { I18n } from "@aws-amplify/core";

afterEach(() => {
  cleanup();
});

describe("Footer", () => {
  it("should render", () => {
    render(<Footer pageTitle="test" />);
    expect(
      screen.getByText(I18n.get("footer.solution.page")),
    ).toBeInTheDocument();
  });

  it("should render with Create title", () => {
    render(<Footer pageTitle="Create" />);
    expect(
      screen.getByText(I18n.get("footer.solution.ig")),
    ).toBeInTheDocument();
  });
});
