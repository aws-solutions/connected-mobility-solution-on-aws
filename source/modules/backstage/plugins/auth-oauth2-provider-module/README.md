# OAuth 2.0 Provider Backend Module

The oauth2-provider backend module for the auth plugin provides generic OAuth 2.0 identity provider support
with the option to further customize the sign-in resolver and identity management. For more information on
sign-in and identity management, see the docs: <https://backstage.io/docs/auth/identity-resolver/>

The current implementation creates a user entity ref based on email, and assigns
a Backstage token for that user entity regardless of the entities existence within the Backstage catalog.
