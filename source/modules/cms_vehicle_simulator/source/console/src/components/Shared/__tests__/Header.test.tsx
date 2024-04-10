// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen } from "@testing-library/react";
import Header from "../../../components/Shared/Header";
import { I18n } from "@aws-amplify/core";

describe("Header", () => {
  it("should render", () => {
    render(<Header />);
    expect(screen.getByText(I18n.get("application"))).toBeInTheDocument();
  });
});
