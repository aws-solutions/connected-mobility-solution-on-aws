// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AcdpBuildAction } from "backstage-plugin-acdp-common";
import { z } from "zod";

// NOSONAR
export const startBuildInputSchema = z.object({
  entityRef: z
    .string()
    .regex(
      /^([A-Za-z0-9][-A-Za-z0-9]*):([A-Za-z0-9][-A-Za-z0-9]*|default)\/([A-Za-z0-9_][-A-Za-z0-9_]*)$/,
      "Invalid EntityRef",
    ),
  action: z.nativeEnum(AcdpBuildAction),
});

export type StartBuildInput = z.infer<typeof startBuildInputSchema>;
