// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

// For now all we need is Arn, but later on we might need more information from the Application
export interface AcdpApplication {
  arn?: string;
  applicationTag?: {
    [key: string]: string;
  };
}
