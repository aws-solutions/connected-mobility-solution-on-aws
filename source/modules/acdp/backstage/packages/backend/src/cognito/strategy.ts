// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { OutgoingHttpHeaders } from "http";
import OAuth2Strategy, {
  StrategyOptions,
  VerifyFunction,
} from "passport-oauth2";

export interface CognitoStrategyOptions {
  clientID: string;
  clientSecret: string;
  authDomain: string;
  allowedScopes?: string[];
  callbackURL?: string;
  scopes?: string | string[];
  scopeSeparator?: string;
  passReqToCallback?: false;
  customHeaders?: OutgoingHttpHeaders;
  sessionKey?: string;
  store?: OAuth2Strategy.StateStore;
  state?: any;
  skipUserProfile?: any;
  pkce?: boolean;
  proxy?: any;
}
export class CognitoStrategy extends OAuth2Strategy {
  userInfoURL: string;
  options: CognitoStrategyOptions;
  constructor(options: CognitoStrategyOptions, verify: VerifyFunction) {
    let optionsScopes = [] as string[];

    if (typeof options.scopes === "string") {
      optionsScopes = options.scopes.split(options.scopeSeparator || " ");
    } else {
      if (options.scopes) {
        optionsScopes = options.scopes;
      }
    }
    const optionsWithURLs: StrategyOptions = {
      ...options,
      authorizationURL: `https://${options.authDomain}/oauth2/authorize`,
      tokenURL: `https://${options.authDomain}/oauth2/token`,
      scope: [...(options.allowedScopes || []), ...optionsScopes],
    };
    super(optionsWithURLs, verify);
    this.name = "cognito";
    this.options = options;
    this._oauth2.useAuthorizationHeaderforGET(true);
    this.userInfoURL = `https://${options.authDomain}/oauth2/userInfo`;
  }

  authorizationParams() {
    return {
      audience: this.options.authDomain,
      prompt: "consent",
    };
  }

  userProfile(accessToken: string, done: (err: any, profile?: any) => void) {
    this._oauth2.get(this.userInfoURL, accessToken, (err, body) => {
      if (err) {
        return done(
          new OAuth2Strategy.InternalOAuthError(
            "Failed to fetch user profile",
            err.statusCode,
          ),
        );
      }
      if (!body) {
        return done(
          new Error("Failed to fetch user profile, body cannot be empty"),
        );
      }
      try {
        const json = typeof body !== "string" ? body.toString() : body;
        const profile = CognitoStrategy.parse(json);
        return done(null, profile);
      } catch (e) {
        return done(new Error("Failed to parse user profile"));
      }
    });
  }
  static parse(json: string) {
    const resp = JSON.parse(json);
    return {
      id: resp.account_id,
      provider: "cognito",
      username: resp.nickname,
      displayName: resp.name,
      emails: [{ value: resp.email }],
      photos: [{ value: resp.picture }],
    };
  }
}
