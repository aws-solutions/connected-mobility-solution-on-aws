// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import {
  AuthProviderFactory,
  OAuthState,
  ProfileInfo,
  SignInResolver,
} from "@backstage/plugin-auth-backend";
import { InternalOAuthError } from "passport-oauth2";

import jwtDecoder from "jwt-decode";
import express from "express";
import passport from "passport";
import lodash from "lodash";

export type PassportProfile = passport.Profile & {
  avatarUrl?: string;
};

export type RedirectInfo = {
  url: string;
  status?: number;
};

export const makeProfileInfo = (
  profile: PassportProfile,
  idToken: string,
): ProfileInfo => {
  let email: string | undefined = undefined;
  if (profile.emails && profile.emails.length > 0) {
    const [firstEmail] = profile.emails;
    email = firstEmail.value;
  }

  let picture: string | undefined = undefined;
  if (profile.avatarUrl) {
    picture = profile.avatarUrl;
  } else if (profile.photos && profile.photos.length > 0) {
    const [firstPhoto] = profile.photos;
    picture = firstPhoto.value;
  }

  let displayName: string | undefined =
    profile.displayName ?? profile.username ?? profile.id;

  try {
    const decoded: Record<string, string> = jwtDecoder(idToken);
    email = email ?? decoded.email;
    picture = picture ?? decoded.picture;
    displayName = displayName ?? decoded.name;
  } catch (e) {
    throw new Error(`Failed to parse id token and get profile info, ${e}`);
  }

  return {
    email,
    picture,
    displayName,
  };
};

export const executeRedirectStrategy = async (
  req: express.Request,
  providerStrategy: passport.Strategy,
  options: Record<string, string>,
): Promise<RedirectInfo> => {
  return new Promise((resolve) => {
    const strategy = Object.create(providerStrategy);
    strategy.redirect = (url: string, status?: number) => {
      resolve({ url, status: status ?? undefined });
    };

    strategy.authenticate(req, { ...options });
  });
};

export const encodeState = (state: OAuthState): string => {
  const stateString = new URLSearchParams(
    lodash.pickBy<string>(state, (value) => value !== undefined),
  ).toString();

  return Buffer.from(stateString, "utf-8").toString("hex");
};

export const executeFrameHandlerStrategy = async <Result, PrivateInfo = never>(
  req: express.Request,
  providerStrategy: passport.Strategy,
) => {
  return new Promise<{ result: Result; privateInfo: PrivateInfo }>(
    (resolve, reject) => {
      const strategy = Object.create(providerStrategy);
      strategy.success = (result: any, privateInfo: any) => {
        resolve({ result, privateInfo });
      };
      strategy.fail = (
        info: { type: "success" | "error"; message?: string },
        // _status: number,
      ) => {
        reject(new Error(`Authentication rejected, ${info.message ?? ""}`));
      };
      strategy.error = (error: InternalOAuthError) => {
        let message = `Authentication failed, ${error.message}`;

        if (error.oauthError?.data) {
          try {
            const errorData = JSON.parse(error.oauthError.data);

            if (errorData.message) {
              message += ` - ${errorData.message}`;
            }
          } catch (parseError) {
            message += ` - ${error.oauthError}`;
          }
        }

        reject(new Error(message));
      };
      strategy.redirect = () => {
        reject(new Error("Unexpected redirect"));
      };
      strategy.authenticate(req, {});
    },
  );
};

type RefreshTokenResponse = {
  /**
   * An access token issued for the signed in user.
   */
  accessToken: string;
  /**
   * Optionally, the server can issue a new Refresh Token for the user
   */
  refreshToken?: string;
  params: any;
};

export const executeRefreshTokenStrategy = async (
  providerStrategy: passport.Strategy,
  refreshToken: string,
  scope: string,
): Promise<RefreshTokenResponse> => {
  return new Promise((resolve, reject) => {
    const anyStrategy = providerStrategy as any;
    const OAuth2 = anyStrategy._oauth2.constructor;
    const oauth2 = new OAuth2(
      anyStrategy._oauth2._clientId,
      anyStrategy._oauth2._clientSecret,
      anyStrategy._oauth2._baseSite,
      anyStrategy._oauth2._authorizeUrl,
      anyStrategy._refreshURL || anyStrategy._oauth2._accessTokenUrl,
      anyStrategy._oauth2._customHeaders,
    );

    oauth2.getOAuthAccessToken(
      refreshToken,
      {
        scope,
        grant_type: "refresh_token",
      },
      (
        err: Error | null,
        accessToken: string,
        newRefreshToken: string,
        params: any,
      ) => {
        if (err) {
          reject(new Error(`Failed to refresh access token ${err.toString()}`));
        }
        if (!accessToken) {
          reject(
            new Error(
              `Failed to refresh access token, no access token received`,
            ),
          );
        }

        resolve({
          accessToken,
          refreshToken: newRefreshToken,
          params,
        });
      },
    );
  });
};

type ProviderStrategy = {
  userProfile(accessToken: string, callback: Function): void;
};

export const executeFetchUserProfileStrategy = async (
  providerStrategy: passport.Strategy,
  accessToken: string,
): Promise<PassportProfile> => {
  return new Promise((resolve, reject) => {
    const anyStrategy = providerStrategy as unknown as ProviderStrategy;
    anyStrategy.userProfile(
      accessToken,
      (error: Error, rawProfile: PassportProfile) => {
        if (error) {
          reject(error);
        } else {
          resolve(rawProfile);
        }
      },
    );
  });
};

/**
 * Creates a standardized representation of an integration with a third-party
 * auth provider.
 *
 * The returned object facilitates the creation of provider instances, and
 * supplies built-in sign-in resolvers for the specific provider.
 */
export function createAuthProviderIntegration<
  TCreateOptions extends unknown[],
  TResolvers extends {
    [name in string]: (...args: any[]) => SignInResolver<any>;
  },
>(config: {
  create: (...args: TCreateOptions) => AuthProviderFactory;
  resolvers?: TResolvers;
}): Readonly<{
  create: (...args: TCreateOptions) => AuthProviderFactory;
  // If no resolvers are defined, this receives the type `never`
  resolvers: Readonly<string extends keyof TResolvers ? never : TResolvers>;
}> {
  return Object.freeze({
    ...config,
    resolvers: Object.freeze(config.resolvers ?? ({} as any)),
  });
}
