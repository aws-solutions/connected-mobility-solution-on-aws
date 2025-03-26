// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React from "react";

import { ToolsContent } from "./interfaces";

export const TOOLS_CONTENT: Record<string, Record<string, ToolsContent>> = {
  decoderManifest: {
    default: {
      title: "Select decoder manifest",
      content: (
        <div>
          <p>TODO: fill info here.</p>
        </div>
      ),
      links: [],
    },
  },
  attributes: {
    default: {
      title: "Specify vehicle attributes",
      content: (
        <div>
          <p>TODO: fill info here.</p>
        </div>
      ),
      links: [],
    },
  },
  fleet: {
    default: {
      title: "Associate fleet",
      content: (
        <div>
          <p>TODO: fill info here.</p>
        </div>
      ),
      links: [],
    },
  },
  review: {
    default: {
      title: "Review and Create",
      content: (
        <div>
          <p>TODO: fill info here.</p>
        </div>
      ),
      links: [],
    },
  },
};
