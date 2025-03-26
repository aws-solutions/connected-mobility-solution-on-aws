// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { FieldExtensionComponentProps } from "@backstage/plugin-scaffolder-react";
import FormControl from "@material-ui/core/FormControl";
import FormHelperText from "@material-ui/core/FormHelperText";
import InputLabel from "@material-ui/core/InputLabel";
import Select from "@material-ui/core/Select";
import { MenuItem } from "@material-ui/core";
import { useQuery } from "@tanstack/react-query";
import { useApi } from "@backstage/core-plugin-api";
import { acdpAccountDirectoryApiRef } from "../../api/AcdpAccountDirectoryApi";

export const AwsRegionComponentContent = ({
  rawErrors,
  required,
  formData,
  onChange,
}: FieldExtensionComponentProps<string>) => {
  const api = useApi(acdpAccountDirectoryApiRef);
  const [availableRegions, setAvailableRegions] = useState(Array<string>);
  const [targetRegion, setTargetRegion] = useState("");

  const handleRegionChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setTargetRegion(event.target.value as string);
    onChange(event.target.value as string);
  };

  useQuery({
    queryKey: ["getAvailableRegions"],
    queryFn: async () => {
      const availableRegionsResponse = await api.getAvailableRegions();

      if (!availableRegionsResponse)
        throw new Error("No Regions available for deployment");

      setAvailableRegions([...new Set(availableRegionsResponse)]);
      return availableRegionsResponse;
    },
    enabled: true,
  });

  return (
    <FormControl
      margin="normal"
      required={required}
      error={rawErrors?.length > 0 && !formData}
    >
      <InputLabel htmlFor="targetAwsAccountRegion" shrink>
        Target Region
      </InputLabel>
      <Select
        labelId="target-region"
        id="target-region-select"
        value={targetRegion}
        onChange={handleRegionChange}
        data-testid="targetAwsRegionSelectComponenet"
      >
        {availableRegions.map((availableRegion: string) => (
          <MenuItem key={availableRegion} value={availableRegion}>
            {availableRegion}
          </MenuItem>
        ))}
      </Select>
      <FormHelperText id="awsRegionHelperText">
        Select an AWS Region from the list
      </FormHelperText>
    </FormControl>
  );
};
