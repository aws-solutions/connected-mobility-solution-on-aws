// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { createBackend } from "@backstage/backend-defaults";

const backend = createBackend();

backend.add(import("@backstage/plugin-auth-backend"));
backend.add(import("@backstage/plugin-auth-backend-module-guest-provider"));
backend.add(import("../src"));

backend.start();
