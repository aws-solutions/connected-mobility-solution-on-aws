// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { render, screen } from "@testing-library/react";
import AttributeFields from "../../../components/DeviceTypeCreate/AttributeFields";
import { I18n } from "@aws-amplify/core";

describe("AttributeFields", () => {
  it("should render", () => {
    render(
      <AttributeFields
        attr={{
          name: "test",
          type: "id",
          default: "test",
        }}
        errors={{}}
        handleFieldFocus={() => {}}
        handleFormChange={() => {}}
        showValidation={[]}
      />,
    );
    expect(screen.getByText(I18n.get("default"))).toBeInTheDocument();
  });
});
