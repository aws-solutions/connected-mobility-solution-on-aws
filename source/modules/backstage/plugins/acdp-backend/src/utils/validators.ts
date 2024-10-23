// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { AcdpBuildAction } from "backstage-plugin-acdp-common";
import { z } from "zod";

// NOSONAR
export const startBuildInputSchema = z.object({
  entityRef: z
    .string()
    .regex(
      /^([A-Za-z0-9][-A-Za-z0-9]*):([A-Za-z0-9][-A-Za-z0-9]*|default)\/(\w[-A-Za-z0-9_]*)$/,
      "Invalid EntityRef",
    ),
  action: z.nativeEnum(AcdpBuildAction),
});

export type StartBuildInput = z.infer<typeof startBuildInputSchema>;

export function isValidEntityRef(entityRef: string): boolean {
  const entityRefPattern = /^[a-zA-Z0-9-_]+:[a-zA-Z0-9-_]+\/[a-zA-Z0-9-_]+$/;

  return entityRefPattern.test(entityRef);
}

export function isValidApplicationArn(arn: string): boolean {
  const applicationArnPattern =
    /^arn:aws:servicecatalog:[a-z]+(-[a-z]+){1,2}-[0-9]{1}:[0-9]{12}:\/applications\/[a-zA-Z0-9-_]{1,256}$/;

  return applicationArnPattern.test(arn);
}
