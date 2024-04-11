// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import type { Config } from "@backstage/config";
import { getBearerTokenFromAuthorizationHeader } from "@backstage/plugin-auth-node";
import { NextFunction, Request, Response, RequestHandler } from "express";
import { PluginEnvironment } from "../types";
import { AuthenticationError } from "@backstage/errors";
import { decodeJwt } from "jose";

function setTokenCookie(
  res: Response,
  options: { token: string; secure: boolean; cookieDomain: string },
) {
  try {
    const payload = decodeJwt(options.token);
    res.cookie("token", options.token, {
      expires: new Date(payload.exp ? payload.exp * 1000 : 0),
      secure: options.secure,
      sameSite: "lax",
      domain: options.cookieDomain,
      path: "/",
      httpOnly: true,
    });
  } catch (_err) {
    // Ignore
  }
}

export const createAuthMiddleware = async (
  config: Config,
  appEnv: PluginEnvironment,
) => {
  const authMiddleware: RequestHandler = async (
    req: Request,
    res: Response,
    next: NextFunction,
  ) => {
    try {
      appEnv.logger.debug(`ALB Headers [${JSON.stringify(req.headers)}]`);
      const token =
        getBearerTokenFromAuthorizationHeader(req.headers.authorization) ||
        (req.cookies?.token as string | undefined) ||
        (req.headers["x-amzn-oidc-data"] as string | undefined);

      if (!token) {
        res.status(401).send("Unauthorized");
        return;
      }
      if (!req.headers.authorization) {
        // getIdentity only seems to work off this header, coalesce all token options to this
        req.headers.authorization = `Bearer ${token}`;
      }

      try {
        //detect backend service generated call and approve
        await appEnv.tokenManager.authenticate(token);
        appEnv.logger.debug(`Successfully authenticated as service user`);
        next();
        return;
      } catch (error) {
        if (error instanceof AuthenticationError) {
          appEnv.logger.debug(`Token is not a valid service token`);
        } else {
          //not an expected error for token failure
          throw error;
        }
      }

      req.user = await appEnv.identity.getIdentity({ request: req });

      if (!req.user) {
        throw new Error("getIdentity failed to set user");
      }

      appEnv.logger.debug(`Successfully authenticated as user`);

      if (token && token !== req.cookies?.token) {
        const baseUrl = config.getString("backend.baseUrl");
        const secure = baseUrl.startsWith("https://");
        const cookieDomain = new URL(baseUrl).hostname;

        setTokenCookie(res, {
          token,
          secure,
          cookieDomain,
        });
      }

      next();
    } catch (error) {
      appEnv.logger.debug(`Failed to authenticate: ${error}`, error);
      res.status(401).send("Unauthorized");
    }
  };
  return authMiddleware;
};
