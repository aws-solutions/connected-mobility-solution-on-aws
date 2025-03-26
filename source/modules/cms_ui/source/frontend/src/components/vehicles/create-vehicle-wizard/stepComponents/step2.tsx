// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {
  useState,
  useImperativeHandle,
  forwardRef,
  useRef,
} from "react";
import {
  Container,
  Input,
  FormField,
  SpaceBetween,
} from "@cloudscape-design/components";
import { CreateVehicleFormData } from "../interfaces";

export interface CreateVehicleAttributesInputPanelProps {
  loadHelpPanelContent: any;
  inputData: CreateVehicleFormData;
  setInputData: any;
}

export interface CreateVehicleAttributesInputPanelRef {
  validate: () => boolean;
}

export const CreateVehicleAttributesInputPanel = forwardRef<
  CreateVehicleAttributesInputPanelRef,
  CreateVehicleAttributesInputPanelProps
>(function CreateVehicleAttributesInputPanel(
  { loadHelpPanelContent, inputData, setInputData },
  ref,
) {
  const [errors, setErrors] = useState({
    vin: "",
    make: "",
    model: "",
    year: "",
    licensePlate: "",
  });

  // Refs for scrolling to error fields
  const vinRef = useRef<HTMLDivElement>(null);
  const makeRef = useRef<HTMLDivElement>(null);
  const modelRef = useRef<HTMLDivElement>(null);
  const yearRef = useRef<HTMLDivElement>(null);
  const licensePlateRef = useRef<HTMLDivElement>(null);

  // Validation helper functions
  const validateVin = (vin: string): string => {
    if (!vin.trim()) {
      return "VIN is required.";
    }
    const regex = /^[A-Za-z0-9]+$/;
    if (!regex.test(vin)) {
      return "Invalid VIN. Only alphanumeric characters are allowed.";
    }
    return "";
  };

  const validateMake = (make: string): string => {
    if (!make.trim()) {
      return "Make is required.";
    }
    return "";
  };

  const validateModel = (model: string): string => {
    if (!model.trim()) {
      return "Model is required.";
    }
    return "";
  };

  const validateYear = (year: number): string => {
    if (!year || year <= 0) {
      return "Year is required and must be greater than zero.";
    }
    return "";
  };

  const validateLicensePlate = (plate: string): string => {
    if (!plate.trim()) {
      return "License Plate is required.";
    }
    return "";
  };

  // Validate all fields and scroll to the first error, if any
  const validateAllFields = (): boolean => {
    const vinError = validateVin(inputData.createVehicle.vin || "");
    const makeError = validateMake(inputData.createVehicle.make || "");
    const modelError = validateModel(inputData.createVehicle.model || "");
    const yearError = validateYear(inputData.createVehicle.year || 0);
    const plateError = validateLicensePlate(
      inputData.createVehicle.licensePlate || "",
    );

    setErrors({
      vin: vinError,
      make: makeError,
      model: modelError,
      year: yearError,
      licensePlate: plateError,
    });

    if (vinError) {
      vinRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      return false;
    }
    if (makeError) {
      makeRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      return false;
    }
    if (modelError) {
      modelRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      return false;
    }
    if (yearError) {
      yearRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      return false;
    }
    if (plateError) {
      licensePlateRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      return false;
    }
    return true;
  };

  // Expose the validate method to the parent.
  useImperativeHandle(ref, () => ({
    validate: validateAllFields,
  }));

  return (
    <Container id="attributes-panel" className="custom-screenshot-hide">
      <SpaceBetween size="l">
        <div ref={vinRef}>
          <FormField
            label="VIN"
            description="Vehicle Identification Number"
            constraintText="Valid characters are a-z, A-Z and 0-9."
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.vin}
          >
            <Input
              ariaRequired={true}
              value={inputData.createVehicle.vin ?? ""}
              onChange={({ detail: { value } }) => {
                setInputData({
                  createVehicle: { ...inputData.createVehicle, vin: value },
                });
                setErrors((prev) => ({ ...prev, vin: validateVin(value) }));
              }}
              onBlur={() => {
                const vin = inputData.createVehicle.vin || "";
                setErrors((prev) => ({ ...prev, vin: validateVin(vin) }));
              }}
            />
          </FormField>
        </div>
        <div ref={makeRef}>
          <FormField
            label="Make"
            description="Vehicle Make"
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.make}
          >
            <Input
              ariaRequired={true}
              value={inputData.createVehicle.make ?? ""}
              onChange={({ detail: { value } }) => {
                setInputData({
                  createVehicle: { ...inputData.createVehicle, make: value },
                });
                setErrors((prev) => ({ ...prev, make: validateMake(value) }));
              }}
              onBlur={() => {
                const make = inputData.createVehicle.make || "";
                setErrors((prev) => ({ ...prev, make: validateMake(make) }));
              }}
            />
          </FormField>
        </div>
        <div ref={modelRef}>
          <FormField
            label="Model"
            description="Vehicle Model"
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.model}
          >
            <Input
              ariaRequired={true}
              value={inputData.createVehicle.model ?? ""}
              onChange={({ detail: { value } }) => {
                setInputData({
                  createVehicle: { ...inputData.createVehicle, model: value },
                });
                setErrors((prev) => ({ ...prev, model: validateModel(value) }));
              }}
              onBlur={() => {
                const model = inputData.createVehicle.model || "";
                setErrors((prev) => ({ ...prev, model: validateModel(model) }));
              }}
            />
          </FormField>
        </div>
        <div ref={yearRef}>
          <FormField
            label="Year"
            description="Vehicle Manufacturing Year"
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.year}
          >
            <Input
              ariaRequired={true}
              value={
                inputData.createVehicle.year
                  ? String(inputData.createVehicle.year)
                  : ""
              }
              onChange={({ detail: { value } }) => {
                setInputData({
                  createVehicle: {
                    ...inputData.createVehicle,
                    year: Number(value),
                  },
                });
                setErrors((prev) => ({
                  ...prev,
                  year: validateYear(Number(value)),
                }));
              }}
              onBlur={() => {
                const year = inputData.createVehicle.year || 0;
                setErrors((prev) => ({ ...prev, year: validateYear(year) }));
              }}
            />
          </FormField>
        </div>
        <div ref={licensePlateRef}>
          <FormField
            label="License Plate"
            description="Vehicle License Plate Number"
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.licensePlate}
          >
            <Input
              ariaRequired={true}
              value={inputData.createVehicle.licensePlate ?? ""}
              onChange={({ detail: { value } }) => {
                setInputData({
                  createVehicle: {
                    ...inputData.createVehicle,
                    licensePlate: value,
                  },
                });
                setErrors((prev) => ({
                  ...prev,
                  licensePlate: validateLicensePlate(value),
                }));
              }}
              onBlur={() => {
                const plate = inputData.createVehicle.licensePlate || "";
                setErrors((prev) => ({
                  ...prev,
                  licensePlate: validateLicensePlate(plate),
                }));
              }}
            />
          </FormField>
        </div>
      </SpaceBetween>
    </Container>
  );
});
