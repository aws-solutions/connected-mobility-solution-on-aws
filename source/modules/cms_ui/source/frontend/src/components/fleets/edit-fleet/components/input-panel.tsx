// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect } from "react";
import {
  Container,
  Input,
  FormField,
  SpaceBetween,
  Textarea,
} from "@cloudscape-design/components";
import { EditFleetEntry } from "@com.cms.fleetmanagement/api-client";
import useLocationHash from "../../fleet-management/use-location-hash";

export interface CreateFleetInputPanelProps {
  loadHelpPanelContent: any;
  inputData: EditFleetEntry;
  setInputData: any;
}

export function CreateFleetInputPanel({
  loadHelpPanelContent,
  inputData,
  setInputData,
}: CreateFleetInputPanelProps) {
  const locationHash = useLocationHash();

  useEffect(() => {
    setInputData({ id: locationHash });
  }, []);

  return (
    <Container id="origin-panel" className="custom-screenshot-hide">
      <SpaceBetween size="l">
        <FormField
          label="Fleet Id"
          description="A unique identifier for the fleet."
          constraintText="Valid characters are a-z, A-Z, 0-9, underscores (_) and hypens (-)."
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Input
            ariaRequired={true}
            value={locationHash ?? inputData.id}
            onChange={({ detail: { value } }) => {
              setInputData({ id: value });
            }}
            disabled={true}
          />
        </FormField>
        <FormField
          label="Display Name"
          description="A descriptive display name for the fleet."
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Input
            ariaRequired={true}
            value={inputData.name ?? ""}
            onChange={({ detail: { value } }) => {
              setInputData({ name: value });
            }}
          />
        </FormField>
        <FormField
          label="Description"
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Textarea
            placeholder={"Enter description"}
            value={inputData.description ?? ""}
            onChange={({ detail: { value } }) => {
              setInputData({ description: value });
            }}
          />
        </FormField>
      </SpaceBetween>
    </Container>
  );
}
