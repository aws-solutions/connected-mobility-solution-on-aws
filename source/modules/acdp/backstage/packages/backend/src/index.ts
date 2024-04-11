// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import Router from "express-promise-router";
import { NextFunction, Request, Response, RequestHandler } from "express";
import {
  createServiceBuilder,
  loadBackendConfig,
  getRootLogger,
  useHotMemoize,
  notFoundHandler,
  CacheManager,
  DatabaseManager,
  UrlReaders,
  ServerTokenManager,
  HostDiscovery,
  createLegacyAuthAdapters,
} from "@backstage/backend-common";
import { TaskScheduler } from "@backstage/backend-tasks";
import { Config } from "@backstage/config";
import app from "./plugins/app";
import auth from "./plugins/auth";
import catalog from "./plugins/catalog";
import scaffolder from "./plugins/scaffolder";
import proxy from "./plugins/proxy";
import techdocs from "./plugins/techdocs";
import search from "./plugins/search";
import acdp from "./plugins/acdp";

import cookieParser from "cookie-parser";
import { PluginEnvironment } from "./types";
import { ServerPermissionClient } from "@backstage/plugin-permission-node";
import { DefaultIdentityClient } from "@backstage/plugin-auth-node";
import { createAuthMiddleware } from "./alb-auth/middleware";
import { customErrorHandler } from "./middleware/customErrorHandler";
import { CatalogClient } from "@backstage/catalog-client";
import { ScmIntegrations } from "@backstage/integration";

function makeCreateEnv(config: Config) {
  const root = getRootLogger();
  const reader = UrlReaders.default({ logger: root, config });
  const discovery = HostDiscovery.fromConfig(config);
  const catalogClient = new CatalogClient({
    discoveryApi: discovery,
  });
  const cacheManager = CacheManager.fromConfig(config);
  const databaseManager = DatabaseManager.fromConfig(config, { logger: root });
  const tokenManager = ServerTokenManager.fromConfig(config, { logger: root });
  const taskScheduler = TaskScheduler.fromConfig(config);
  const identity = DefaultIdentityClient.create({
    discovery,
    algorithms: ["RS256", "ES256", "HS256"],
  });
  const permissions = ServerPermissionClient.fromConfig(config, {
    discovery,
    tokenManager,
  });

  const { auth, httpAuth } = createLegacyAuthAdapters({
    auth: undefined,
    httpAuth: undefined,
    discovery: discovery,
    identity: identity,
  });

  root.info(`Created UrlReader ${reader}`);

  return (plugin: string): PluginEnvironment => {
    const logger = root.child({ type: "plugin", plugin });
    const database = databaseManager.forPlugin(plugin);
    const cache = cacheManager.forPlugin(plugin);
    const scheduler = taskScheduler.forPlugin(plugin);
    const integrations = ScmIntegrations.fromConfig(config);
    return {
      auth,
      httpAuth,
      logger,
      database,
      cache,
      catalogClient,
      config,
      discovery,
      identity,
      integrations,
      permissions,
      reader,
      scheduler,
      tokenManager,
    };
  };
}

async function main() {
  const config = await loadBackendConfig({
    argv: process.argv,
    logger: getRootLogger(),
  });
  const createEnv = makeCreateEnv(config);

  const catalogEnv = useHotMemoize(module, () => createEnv("catalog"));
  const scaffolderEnv = useHotMemoize(module, () => createEnv("scaffolder"));
  const authEnv = useHotMemoize(module, () => createEnv("auth"));
  const proxyEnv = useHotMemoize(module, () => createEnv("proxy"));
  const techdocsEnv = useHotMemoize(module, () => createEnv("techdocs"));
  const searchEnv = useHotMemoize(module, () => createEnv("search"));
  const appEnv = useHotMemoize(module, () => createEnv("app"));
  const acdpEnv = useHotMemoize(module, () => createEnv("acdp-backend"));

  let authMiddleware: RequestHandler | undefined = undefined;
  if (authEnv.config.getOptional("auth.environment") === "development") {
    authMiddleware = async (_: Request, __: Response, next: NextFunction) => {
      next();
    };
  } else {
    authMiddleware = await createAuthMiddleware(config, appEnv);
  }

  const customErrorHandlerMiddleware = customErrorHandler({
    showStackTraces: false,
  });

  const apiRouter = Router();
  apiRouter.use(cookieParser());
  apiRouter.use("/auth", await auth(authEnv));
  apiRouter.use("/cookie", authMiddleware, (_req, res) => {
    res.status(200).send(`Coming right up`);
  });
  apiRouter.use("/scaffolder", authMiddleware, await scaffolder(scaffolderEnv));
  apiRouter.use("/catalog", authMiddleware, await catalog(catalogEnv));
  apiRouter.use("/techdocs", authMiddleware, await techdocs(techdocsEnv));
  apiRouter.use("/proxy", authMiddleware, await proxy(proxyEnv));
  apiRouter.use("/search", authMiddleware, await search(searchEnv));
  apiRouter.use("/acdp-backend", authMiddleware, await acdp(acdpEnv));

  apiRouter.use(authMiddleware, notFoundHandler());
  // customErrorHandlerMiddleware must be the last middleware to function
  apiRouter.use(customErrorHandlerMiddleware);

  const service = createServiceBuilder(module)
    .loadConfig(config)
    .addRouter("/api", apiRouter)
    .addRouter("", await app(appEnv));

  await service.start().catch((err) => {
    console.log(err);
    process.exit(1);
  });
}

module.hot?.accept();
main().catch((error) => {
  console.error("Backend failed to start up", error);
  process.exit(1);
});

declare global {
  namespace Express {
    interface User {
      token?: string;
      fullProfile?: any;
      accessToken?: string;
      refreshToken?: string;
      params?: any;
    }
  }
}
