// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { FieldExtensionComponentProps } from "@backstage/plugin-scaffolder-react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AwsAccountIdComponentContent } from "./AwsAccountIdComponentContent";

const queryClient = new QueryClient();

export const AwsAccountIdComponent = (
  props: FieldExtensionComponentProps<string>,
) => {
  return (
    <QueryClientProvider client={queryClient}>
      <AwsAccountIdComponentContent {...props} />
    </QueryClientProvider>
  );
};
