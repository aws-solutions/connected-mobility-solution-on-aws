// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { createTemplateAction } from "@backstage/plugin-scaffolder-node";
import * as yaml from "yaml";
import { z } from "zod";
import * as fs from "fs";

export const createNewYamlFileAction = () => {
  return createTemplateAction({
    id: "aws:fs:write-yaml",
    description: "Writes the input as a workspace file",
    schema: {
      input: z.object({
        filename: z.string().describe("The filename to write"),
        entity: z.record(z.any()).describe("YAML body for the file content"),
      }),
      output: {
        type: "object",
        properties: {
          filePath: {
            title: "Workspace path file was written to",
            type: "string",
          },
        },
      },
    },

    async handler(ctx) {
      const filepath = `${ctx.workspacePath}/${ctx.input.filename}`;

      fs.writeFileSync(filepath, yaml.stringify(ctx.input.entity));

      ctx.logger.info(`Successfully created file: ${ctx.input.filename}`);

      ctx.output("filename", ctx.input.filename);
    },
  });
};
