// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  createBackendModule,
  coreServices,
} from "@backstage/backend-plugin-api";
import {
  DocsBuildStrategy,
  techdocsBuildsExtensionPoint,
} from "@backstage/plugin-techdocs-node";

export const techdocsModuleCustomBuildStrategy = createBackendModule({
  pluginId: "techdocs",
  moduleId: "custom-build-strategy",
  register(env) {
    env.registerInit({
      deps: {
        config: coreServices.rootConfig,
        logger: coreServices.logger,
        techdocs: techdocsBuildsExtensionPoint,
      },
      async init({ config, logger, techdocs }) {
        logger.info(
          "Initializing custom build strategy module, extension of the techdocs plugin.",
        );

        const docsBuildStrategy: DocsBuildStrategy = {
          shouldBuild: async (params) => {
            const shouldBuildAnnotation =
              params.entity.metadata?.annotations?.[
                "aws.amazon.com/techdocs-builder"
              ];

            if (shouldBuildAnnotation !== undefined)
              return shouldBuildAnnotation === "local";

            return config.getString("techdocs.builder") === "local";
          },
        };

        techdocs.setBuildStrategy(docsBuildStrategy);
      },
    });
  },
});
