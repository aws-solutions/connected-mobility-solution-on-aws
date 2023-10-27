// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/* eslint-disable no-cond-assign */
import {
  AuthHandler,
  AuthResolverContext,
  encodeState,
  OAuthAdapter,
  OAuthEnvironmentHandler,
  OAuthHandlers,
  OAuthRefreshRequest,
  OAuthResponse,
  OAuthResult,
  OAuthStartRequest,
  SignInResolver,
} from '@backstage/plugin-auth-backend';

import {
  createAuthProviderIntegration,
  executeFetchUserProfileStrategy,
  executeFrameHandlerStrategy,
  executeRedirectStrategy,
  executeRefreshTokenStrategy,
  makeProfileInfo,
} from './helpers';

import { CognitoStrategy } from './strategy';
import express from 'express';
import { fetchClientDetails } from './fetchers';
import { Logger } from 'winston';

export const cognitoDefaultAuthHandler: AuthHandler<any> = async ({
  fullProfile,
  params,
}) => ({
  profile: makeProfileInfo(fullProfile, params.id_token),
});

declare type CognitoAuthProviderOptions = {
  userPoolId: string;
  clientId?: string;
  scopes?: string[];
  callbackURL?: string;
  authHandler: AuthHandler<OAuthResult>;
  signInResolver?: SignInResolver<OAuthResult>;
  resolverContext: AuthResolverContext;
  logger: Logger;
  tokenCookie: string;
};

export class CognitoAuthProvider implements OAuthHandlers {
  userPoolId: string;
  private _strategy: CognitoStrategy;
  private readonly authHandler: AuthHandler<OAuthResult>;
  private readonly signInResolver?: SignInResolver<OAuthResult>;
  private readonly resolverContext: AuthResolverContext;
  private logger: Logger;
  tokenCookie: string;

  constructor({
    userPoolId,
    clientId,
    scopes,
    authHandler,
    signInResolver,
    resolverContext,
    callbackURL,
    logger,
    tokenCookie,
  }: CognitoAuthProviderOptions) {
    this.userPoolId = userPoolId;
    this.authHandler = authHandler;
    this.signInResolver = signInResolver;
    this.resolverContext = resolverContext;
    this.logger = logger;
    this.tokenCookie = tokenCookie;
    if (!this.userPoolId) {
      this.logger.warn(
        `Can't setup Cognito authentication, missing UserPoolId`,
      );
      throw new Error(
        'Cognito Authentication Not Configured: missing user pool id attribute [userPoolId]',
      );
    }

    this._strategy = {} as CognitoStrategy;

    fetchClientDetails(userPoolId, clientId)
      .then(
        ({
          authDomain,
          clientId: poolClientId,
          clientSecret,
          clientScopes,
        }) => {
          logger.info(
            `Creating OAuth2 Strategy for UserPool: ${this.userPoolId} - ClientId: ${poolClientId}`,
          );
          this._strategy = new CognitoStrategy(
            {
              clientID: poolClientId,
              clientSecret,
              callbackURL,
              allowedScopes: clientScopes,
              scopes,
              authDomain,
            },
            (accessToken, refreshToken, params, fullProfile, done) => {
              done(void 0, {
                fullProfile,
                accessToken,
                refreshToken,
                params,
              });
            },
          );
        },
      )
      .catch(ex => {
        throw new Error(
          `Failed to setup cognito authentication: ${ex.message}`,
        );
      });
  }
  async start(req: OAuthStartRequest) {
    return await executeRedirectStrategy(req, this._strategy, {
      state: encodeState(req.state),
    });
  }
  async handler(req: express.Request) {
    const { result } = await executeFrameHandlerStrategy<OAuthResult>(
      req,
      this._strategy,
    );

    const response = await this.handleResult(result);

    req.res?.cookie(this.tokenCookie, response.backstageIdentity?.token, {
      sameSite: 'lax',
      expires: new Date(
        Date.now() + (response.providerInfo.expiresInSeconds || 3600) * 1000,
      ),
    });

    return {
      response,
      refreshToken: result.refreshToken,
    };
  }
  private async handleResult(result: OAuthResult): Promise<OAuthResponse> {
    const { profile } = await this.authHandler(result, this.resolverContext);

    const response: OAuthResponse = {
      providerInfo: {
        idToken: result.params.id_token,
        accessToken: result.accessToken,
        scope: result.params.scope,
        expiresInSeconds: result.params.expires_in,
      },
      profile,
    };

    if (this.signInResolver) {
      response.backstageIdentity = await this.signInResolver(
        {
          result,
          profile,
        },
        this.resolverContext,
      );
    }

    return response;
  }
  async refresh(req: OAuthRefreshRequest) {
    const { accessToken, params, refreshToken } =
      await executeRefreshTokenStrategy(
        this._strategy,
        req.refreshToken,
        req.scope,
      );

    const fullProfile = await executeFetchUserProfileStrategy(
      this._strategy,
      accessToken,
    );

    return {
      response: await this.handleResult({
        fullProfile,
        params,
        accessToken,
      }),
      refreshToken,
    };
  }
}

export const cognito = createAuthProviderIntegration({
  create(options: {
    logger: Logger;
    authHandler?: AuthHandler<OAuthResult>;
    signIn?: {
      resolver: SignInResolver<OAuthResult>;
    };
  }) {
    return ({ providerId, globalConfig, config, resolverContext }) =>
      OAuthEnvironmentHandler.mapConfig(config, envConfig => {
        const userPoolId = envConfig.getString('userPoolId');
        const clientId = envConfig.getOptionalString('clientId');
        const scopes = envConfig.getOptionalStringArray('scopes');
        const customCallbackURL = envConfig.getOptionalString('callbackUrl');
        const tokenCookie =
          envConfig.getOptionalString('auth.cookie') || 'X-Cognito-Token';

        options.logger.info(
          `Creating Cognito Auth Provider for UserPool ${userPoolId} [ClientId: ${
            clientId ?? 'None provided'
          }`,
        );
        const callbackURL =
          customCallbackURL ||
          `${globalConfig.baseUrl}/${providerId}/handler/frame`;

        const authHandler: AuthHandler<OAuthResult> =
          options?.authHandler ?? cognitoDefaultAuthHandler;

        if (!userPoolId) {
          throw new Error(
            'Cognito Auth Configuration error: missing cognito user pool ID [userPoolId].',
          );
        }

        const provider = new CognitoAuthProvider({
          userPoolId,
          clientId,
          scopes,
          callbackURL,
          authHandler,
          signInResolver: options?.signIn?.resolver,
          resolverContext,
          logger: options.logger,
          tokenCookie,
        });

        return OAuthAdapter.fromConfig(globalConfig, provider, {
          providerId,
          callbackUrl: callbackURL,
        });
      });
  },
});

export const createCognitoProvider = cognito.create;
