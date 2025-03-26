// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import {
  Container,
  Input,
  FormField,
  SpaceBetween,
} from "@cloudscape-design/components";
import useLocationHash from "../../fleet-management/use-location-hash";

export function AssociateVehiclesInputPanel() {
  const locationHash = useLocationHash();

  return (
    <Container id="origin-panel" className="custom-screenshot-hide">
      <SpaceBetween size="l">
        <FormField
          label="Fleet Id"
          description="A unique identifier for the fleet."
          constraintText="Valid characters are a-z, A-Z, 0-9, underscores (_) and hypens (-)."
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Input ariaRequired={true} value={locationHash} disabled={true} />
        </FormField>
      </SpaceBetween>
    </Container>
  );
}
