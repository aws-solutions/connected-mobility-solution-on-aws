// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  Box,
  BreadcrumbGroup,
  HelpPanel,
  Icon,
  SpaceBetween,
} from "@cloudscape-design/components";
import { ExternalLinkGroup } from "../commons";
import { LANDING_PAGE_URL } from "../../utils/constants";

export const ToolsContent = () => (
  <HelpPanel
    header={<h2>Fleet Management</h2>}
    footer={
      <ExternalLinkGroup
        items={[
          {
            href: LANDING_PAGE_URL,
            text: "Solution Landing Page",
          },
        ]}
      />
    }
  >
    <SpaceBetween size="s">
      <Box variant="p">Fill in info here...</Box>
    </SpaceBetween>
  </HelpPanel>
);
