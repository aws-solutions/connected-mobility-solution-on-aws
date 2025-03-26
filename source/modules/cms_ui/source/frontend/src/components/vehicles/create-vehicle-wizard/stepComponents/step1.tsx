// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, {
  useState,
  useCallback,
  useContext,
  useImperativeHandle,
  forwardRef,
  useRef,
  useEffect,
} from "react";
import {
  Container,
  Input,
  FormField,
  SpaceBetween,
  Select,
  SelectProps,
} from "@cloudscape-design/components";
import { InfoLink } from "../../../commons";
import { ApiContext } from "@/api/provider";
import { ListDecoderManifestsCommand } from "@com.cms.fleetmanagement/api-client";
import { CreateVehicleFormData } from "../interfaces";

type StatusType = "pending" | "loading" | "finished" | "error";

export interface CreateVehicleInputPanelProps {
  loadHelpPanelContent: any;
  inputData: CreateVehicleFormData;
  setInputData: any;
  // Props for persisting options during the wizard
  options?: SelectProps.Option[];
  setOptions?: React.Dispatch<React.SetStateAction<SelectProps.Option[]>>;
}

export interface CreateVehicleInputPanelRef {
  validate: () => boolean;
}

export const CreateVehicleInputPanel = forwardRef<
  CreateVehicleInputPanelRef,
  CreateVehicleInputPanelProps
>(function CreateVehicleInputPanel(
  { loadHelpPanelContent, inputData, setInputData, options, setOptions },
  ref,
) {
  const [localOptions, setLocalOptions] = useState<SelectProps.Option[]>([]);
  const optionsToUse = options ?? localOptions;
  const setOptionsToUse = setOptions ?? setLocalOptions;

  const [selectedOption, setSelectedOption] = useState<SelectProps.Option>();
  const [status, setStatus] = useState<StatusType>("pending");
  const [errors, setErrors] = useState({
    name: "",
    decoderManifestName: "",
  });

  const api = useContext(ApiContext);

  const vehicleNameRef = useRef<HTMLDivElement>(null);
  const decoderManifestRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async () => {
    try {
      const cmd = new ListDecoderManifestsCommand();
      const output = await api.client.send(cmd);
      setStatus("finished");
      const newOptions = (output.decoderManifests || []).map(
        (decoderManifest) => ({
          label: decoderManifest.name,
          value: {
            decoderManifestArn: decoderManifest.arn,
            modelManifestArn: decoderManifest.modelManifestArn,
            decoderManifestName: decoderManifest.name,
          },
        }),
      );
      setOptionsToUse(newOptions);
    } catch (error) {
      setStatus("error");
    }
  }, [api.client, setOptionsToUse]);

  // Lazy load on first open...
  const handleLoadItems = useCallback(
    ({ detail: {} }) => {
      if (optionsToUse.length === 0) {
        setStatus("loading");
        fetchData();
      }
    },
    [fetchData, optionsToUse],
  );

  useEffect(() => {
    if (
      inputData.createVehicle.decoderManifestName &&
      optionsToUse.length === 0
    ) {
      fetchData();
    }
  }, [inputData.createVehicle.decoderManifestName, optionsToUse, fetchData]);

  useEffect(() => {
    if (
      inputData.createVehicle.decoderManifestName &&
      optionsToUse.length > 0
    ) {
      const matchingOption = optionsToUse.find(
        (option) =>
          option.value?.decoderManifestName ===
          inputData.createVehicle.decoderManifestName,
      );
      if (matchingOption) {
        setSelectedOption(matchingOption);
      }
    }
  }, [inputData.createVehicle.decoderManifestName, optionsToUse]);

  const validateVehicleName = (name: string): string => {
    if (!name.trim()) {
      return "Vehicle Name is required.";
    }
    const regex = /^[A-Za-z0-9_\-: ]+$/;
    if (!regex.test(name)) {
      return "Invalid characters. Valid characters are a-z, A-Z, 0-9, underscores (_), hypens (-) and colons (:).";
    }
    return "";
  };

  const validateDecoderManifestName = (manifestName: string): string => {
    if (!manifestName || !manifestName.trim()) {
      return "Decoder Manifest is required.";
    }
    return "";
  };

  const validateAllFields = (): boolean => {
    const nameError = validateVehicleName(inputData.createVehicle.name || "");
    const manifestError = validateDecoderManifestName(
      inputData.createVehicle.decoderManifestName || "",
    );

    setErrors({
      name: nameError,
      decoderManifestName: manifestError,
    });

    if (nameError) {
      vehicleNameRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      return false;
    }
    if (manifestError) {
      decoderManifestRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      return false;
    }
    return true;
  };

  useImperativeHandle(ref, () => ({
    validate: validateAllFields,
  }));

  return (
    <Container id="origin-panel" className="custom-screenshot-hide">
      <SpaceBetween size="l">
        <div ref={vehicleNameRef}>
          <FormField
            label="Vehicle Name"
            description="A unique identifier for the vehicle."
            constraintText="Valid characters are a-z, A-Z, 0-9, underscores (_), hypens (-) and colons (:)."
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.name}
          >
            <Input
              ariaRequired={true}
              value={inputData.createVehicle.name ?? ""}
              onChange={({ detail: { value } }) => {
                setInputData({
                  createVehicle: { ...inputData.createVehicle, name: value },
                });
                setErrors((prev) => ({
                  ...prev,
                  name: validateVehicleName(value),
                }));
              }}
              onBlur={() => {
                const name = inputData.createVehicle.name || "";
                setErrors((prev) => ({
                  ...prev,
                  name: validateVehicleName(name),
                }));
              }}
            />
          </FormField>
        </div>
        <div ref={decoderManifestRef}>
          <FormField
            label="Decoder Manifest Name"
            info={
              <InfoLink
                id="content-origin-info-link"
                onFollow={() => loadHelpPanelContent(5)}
              />
            }
            description="The Amazon Resource Name (ARN) of a IoT FleetWise decoder manifest."
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={errors.decoderManifestName}
          >
            <Select
              options={optionsToUse}
              selectedOption={selectedOption ?? null}
              selectedAriaLabel="Selected"
              statusType={status}
              placeholder="Choose a decoder manifest"
              loadingText="Loading decoder manifests"
              errorText="Error fetching decoder manifests"
              recoveryText="Retry"
              empty="No decoder manifests."
              ariaRequired={true}
              onChange={({ detail: { selectedOption } }) => {
                setInputData({
                  createVehicle: {
                    ...inputData.createVehicle,
                    decoderManifestName:
                      selectedOption.value?.decoderManifestName,
                  },
                });
                setSelectedOption(selectedOption);
                setErrors((prev) => ({
                  ...prev,
                  decoderManifestName: validateDecoderManifestName(
                    selectedOption.value?.decoderManifestName || "",
                  ),
                }));
              }}
              onBlur={() => {
                const manifestName =
                  inputData.createVehicle.decoderManifestName || "";
                setErrors((prev) => ({
                  ...prev,
                  decoderManifestName:
                    validateDecoderManifestName(manifestName),
                }));
              }}
              onLoadItems={handleLoadItems}
            />
          </FormField>
        </div>
      </SpaceBetween>
    </Container>
  );
});
