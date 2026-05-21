export const environment = {
  production: true,
  devMode: false,
  apiUrl: '/api',
  msalConfig: {
    auth: {
      clientId: 'f55271c9-f468-4a6d-a7fa-576b96b6bdeb',
      authority: 'https://login.microsoftonline.com/fe990d52-55f3-437e-9b9a-7192d2f17c9f',
      // TODO: Replace with the actual production domain before deploying.
      redirectUri: 'https://PRODUCTION_DOMAIN/auth/finish',
      postLogoutRedirectUri: 'https://PRODUCTION_DOMAIN/login',
      navigateToLoginRequestUrl: false,
    },
  },
  apiScopes: ['api://f55271c9-f468-4a6d-a7fa-576b96b6bdeb/access_as_user'],
};
