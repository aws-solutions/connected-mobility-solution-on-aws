// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { FieldExtensionComponentProps } from "@backstage/plugin-scaffolder-react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AwsRegionComponentContent } from "./AwsRegionComponentContent";

const queryClient = new QueryClient();

export const AwsRegionComponent = (
  props: FieldExtensionComponentProps<string>,
) => {
  return (
    <QueryClientProvider client={queryClient}>
      <AwsRegionComponentContent {...props} />
    </QueryClientProvider>
  );
};
