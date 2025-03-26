// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import {
  Container,
  Input,
  FormField,
  SpaceBetween,
  Header,
} from "@cloudscape-design/components";
import { EditVehicleEntry } from "@com.cms.fleetmanagement/api-client";

export interface CreateVehicleAttributesInputPanelProps {
  loadHelpPanelContent: any;
  inputData: EditVehicleEntry;
  setInputData: any;
}

export function CreateVehicleAttributesInputPanel({
  loadHelpPanelContent,
  inputData,
  setInputData,
}: CreateVehicleAttributesInputPanelProps) {
  return (
    <Container
      id="origin-panel"
      className="custom-screenshot-hide"
      header={<Header variant="h2">Vehicle Attributes</Header>}
    >
      <SpaceBetween size="l">
        <FormField
          label="VIN"
          description="Vehicle Identification Number"
          constraintText="Valid characters are a-z, A-Z and 0-9."
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Input
            ariaRequired={true}
            value={inputData.vin ?? ""}
            onChange={({ detail: { value } }) => {
              setInputData({ vin: value });
            }}
          />
        </FormField>
        <FormField
          label="Make"
          description="Vehicle Make"
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Input
            ariaRequired={true}
            value={inputData.make ?? ""}
            onChange={({ detail: { value } }) => {
              setInputData({ make: value });
            }}
          />
        </FormField>
        <FormField
          label="Model"
          description="Vehicle Model"
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Input
            ariaRequired={true}
            value={inputData.model ?? ""}
            onChange={({ detail: { value } }) => {
              setInputData({ model: value });
            }}
          />
        </FormField>
        <FormField
          label="Year"
          description="Vehicle Manufacturing Year"
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Input
            ariaRequired={true}
            value={String(inputData.year ?? 0)}
            onChange={({ detail: { value } }) => {
              setInputData({ year: Number(value) });
            }}
          />
        </FormField>
        <FormField
          label="License Plate"
          description="Vehicle License Plate Number"
          i18nStrings={{ errorIconAriaLabel: "Error" }}
        >
          <Input
            ariaRequired={true}
            value={inputData.licensePlate ?? ""}
            onChange={({ detail: { value } }) => {
              setInputData({ licensePlate: value });
            }}
          />
        </FormField>
      </SpaceBetween>
    </Container>
  );
}
