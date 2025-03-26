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
  FormField,
  SpaceBetween,
  Select,
  SelectProps,
} from "@cloudscape-design/components";
import { InfoLink } from "../../../commons";
import { ApiContext } from "@/api/provider";
import { ListFleetsCommand } from "@com.cms.fleetmanagement/api-client";
import { CreateVehicleFormData } from "../interfaces";

export interface AssociateVehicleFleetPanelProps {
  loadHelpPanelContent: any;
  inputData: CreateVehicleFormData;
  setInputData: any;
  // Optional props for persisting options during the wizard session
  options?: SelectProps.Option[];
  setOptions?: React.Dispatch<React.SetStateAction<SelectProps.Option[]>>;
}

export interface AssociateVehicleFleetPanelRef {
  validate: () => boolean;
}

export const AssociateVehicleFleetPanel = forwardRef<
  AssociateVehicleFleetPanelRef,
  AssociateVehicleFleetPanelProps
>(function AssociateVehicleFleetPanel(
  { loadHelpPanelContent, inputData, setInputData, options, setOptions },
  ref,
) {
  // Use parent's options if provided; otherwise, maintain local state.
  const [localOptions, setLocalOptions] = useState<SelectProps.Option[]>([]);
  const optionsToUse = options ?? localOptions;
  const setOptionsToUse = setOptions ?? setLocalOptions;

  const [selectedOption, setSelectedOption] = useState<SelectProps.Option>();
  const [status, setStatus] = useState<
    "pending" | "loading" | "finished" | "error"
  >("pending");
  const [error, setError] = useState("");

  const api = useContext(ApiContext);
  const fieldRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async () => {
    try {
      const cmd = new ListFleetsCommand();
      const output = await api.client.send(cmd);
      setStatus("finished");
      const newOptions = (output.fleets || []).map((fleet) => ({
        label: fleet.name,
        value: fleet.id,
      }));
      setOptionsToUse(newOptions);
    } catch (error) {
      setStatus("error");
    }
  }, [api.client, setOptionsToUse]);

  // Lazy load on first open.
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
    if (inputData.associateFleet.id && optionsToUse.length === 0) {
      fetchData();
    }
  }, [inputData.associateFleet.id, optionsToUse, fetchData]);

  useEffect(() => {
    if (inputData.associateFleet.id && optionsToUse.length > 0) {
      const matchingOption = optionsToUse.find(
        (option) => option.value === inputData.associateFleet.id,
      );
      if (matchingOption) {
        setSelectedOption(matchingOption);
      }
    }
  }, [inputData.associateFleet.id, optionsToUse]);

  const validateFleet = (optionToValidate?: SelectProps.Option): string => {
    const option = optionToValidate || selectedOption;
    if (!option || !option.value) {
      return "Fleet selection is required.";
    }
    return "";
  };

  const validateAllFields = (): boolean => {
    const fleetError = validateFleet();
    setError(fleetError);
    if (fleetError) {
      fieldRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
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
        <div ref={fieldRef}>
          <FormField
            label="Fleet"
            info={
              <InfoLink
                id="content-origin-info-link"
                onFollow={() => loadHelpPanelContent(5)}
              />
            }
            description="The unique identifier of a fleet."
            i18nStrings={{ errorIconAriaLabel: "Error" }}
            errorText={error}
          >
            <Select
              options={optionsToUse}
              selectedOption={selectedOption ?? null}
              selectedAriaLabel="Selected"
              statusType={status}
              placeholder="Choose a fleet"
              loadingText="Loading fleets"
              errorText="Error fetching fleet"
              recoveryText="Retry"
              empty="No fleets."
              ariaRequired={true}
              onChange={({ detail: { selectedOption } }) => {
                setSelectedOption(selectedOption);
                setInputData({
                  associateFleet: {
                    id: selectedOption?.value,
                    vehicleNames: [inputData.createVehicle.name],
                  },
                });
                setError(validateFleet(selectedOption));
              }}
              onBlur={() => {
                setError(validateFleet());
              }}
              onLoadItems={handleLoadItems}
            />
          </FormField>
        </div>
      </SpaceBetween>
    </Container>
  );
});
