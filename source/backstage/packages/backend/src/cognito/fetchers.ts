// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { CognitoIdentityProvider } from '@aws-sdk/client-cognito-identity-provider';

const cognitoClient = new CognitoIdentityProvider({});

export interface OAuthClientInfo {
  clientId: string;
  clientSecret: string;
  clientScopes?: string[];
  authDomain: string;
}

export const fetchFirstClient = async (userPoolId: string) => {
  const poolClients = await cognitoClient.listUserPoolClients({
    UserPoolId: userPoolId,
  });
  if (
    !poolClients.UserPoolClients ||
    poolClients.UserPoolClients.length === 0
  ) {
    throw new Error(
      `Failed to fetch client list for pool ${userPoolId}. Make sure the user pool has a client configured.`,
    );
  }
  return poolClients.UserPoolClients[0].ClientId!;
};

export const fetchClientDetails = async (
  userPoolId: string,
  clientId?: string,
): Promise<OAuthClientInfo> => {
  const poolClientId = clientId || (await fetchFirstClient(userPoolId));
  const poolInfo = await cognitoClient.describeUserPool({
    UserPoolId: userPoolId,
  });
  const clientInfo = await cognitoClient.describeUserPoolClient({
    UserPoolId: userPoolId,
    ClientId: poolClientId,
  });
  const authDomain =
    poolInfo.UserPool?.CustomDomain || poolInfo.UserPool?.Domain;
  if (!clientInfo.UserPoolClient?.ClientSecret || !authDomain) {
    throw new Error(`Failed to fetch client secret or cognito userpool domain`);
  }
  return {
    clientId: poolClientId,
    clientSecret: clientInfo.UserPoolClient?.ClientSecret!,
    clientScopes: clientInfo.UserPoolClient?.AllowedOAuthScopes,
    authDomain,
  };
};
