// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { scaffolderPlugin } from "@backstage/plugin-scaffolder";
import { createScaffolderFieldExtension } from "@backstage/plugin-scaffolder-react";
import { AwsAccountIdComponent } from "../components/AwsAccountIdComponent";
import { AwsRegionComponent } from "../components/AwsRegionComponent";

export const AwsAccountIdFieldExtension = scaffolderPlugin.provide(
  createScaffolderFieldExtension({
    name: "AwsAccountId",
    component: AwsAccountIdComponent,
  }),
);

export const AwsRegionFieldExtension = scaffolderPlugin.provide(
  createScaffolderFieldExtension({
    name: "AwsRegion",
    component: AwsRegionComponent,
  }),
);
