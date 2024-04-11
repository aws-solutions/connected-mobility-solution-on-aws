// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  createRouter,
  Generators,
  Preparers,
  Publisher,
  TechdocsGenerator,
} from "@backstage/plugin-techdocs-backend";
import { Router } from "express";
import { PluginEnvironment } from "../types";
import { Config } from "@backstage/config";
import { Entity } from "@backstage/catalog-model";
import { DocsBuildStrategy } from "@backstage/plugin-techdocs-node";

export class AnnotationBasedBuildStrategy implements DocsBuildStrategy {
  private readonly config: Config;

  constructor(config: Config) {
    this.config = config;
  }

  async shouldBuild(params: { entity: Entity }): Promise<boolean> {
    let shouldBuildAnnotation =
      params.entity.metadata?.annotations?.["aws.amazon.com/techdocs-builder"];

    if (shouldBuildAnnotation !== undefined)
      return shouldBuildAnnotation === "local";

    return this.config.getString("techdocs.builder") === "local";
  }
}

export default async function createPlugin(
  env: PluginEnvironment,
): Promise<Router> {
  // Preparers are responsible for fetching source files for documentation.
  const preparers = await Preparers.fromConfig(env.config, {
    logger: env.logger,
    reader: env.reader,
  });

  const generators = new Generators();

  const techdocsGenerator = TechdocsGenerator.fromConfig(env.config, {
    logger: env.logger,
  });
  generators.register("techdocs", techdocsGenerator);

  // Publisher is used for
  // 1. Publishing generated files to storage
  // 2. Fetching files from storage and passing them to TechDocs frontend.
  const publisher = await Publisher.fromConfig(env.config, {
    logger: env.logger,
    discovery: env.discovery,
  });

  // checks if the publisher is working and logs the result
  await publisher.getReadiness();

  return await createRouter({
    preparers,
    generators,
    publisher,
    logger: env.logger,
    config: env.config,
    discovery: env.discovery,
    cache: env.cache,
    docsBuildStrategy: new AnnotationBasedBuildStrategy(env.config),
    auth: env.auth,
    httpAuth: env.httpAuth,
  });
}
