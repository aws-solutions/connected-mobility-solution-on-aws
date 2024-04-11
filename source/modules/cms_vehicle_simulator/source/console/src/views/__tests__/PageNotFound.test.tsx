// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen } from "@testing-library/react";

import PageNotFound from "../../views/PageNotFound";
import { I18n } from "@aws-amplify/core";

describe("PageNotFound", () => {
  it("should render", () => {
    render(<PageNotFound />);
    expect(
      screen.getByText(`${I18n.get("page.not.found")}:`),
    ).toBeInTheDocument();
  });
});
