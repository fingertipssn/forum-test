import {
  MSAL_GUARD_CONFIG,
  MSAL_INSTANCE,
  MsalBroadcastService,
  MsalGuard,
  MsalService,
  MsalGuardConfiguration,
} from '@azure/msal-angular';
import {
  BrowserCacheLocation,
  InteractionType,
  LogLevel,
  PublicClientApplication,
  type IPublicClientApplication,
} from '@azure/msal-browser';
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { AzureAuthInterceptor } from './azure-auth.interceptor';

export function msalInstanceFactory(): IPublicClientApplication {
  return new PublicClientApplication({
    auth: {
      clientId: environment.msalConfig.auth.clientId,
      authority: environment.msalConfig.auth.authority,
      redirectUri: environment.msalConfig.auth.redirectUri,
      postLogoutRedirectUri: environment.msalConfig.auth.postLogoutRedirectUri,
      // No redirigir de vuelta al URL que inició el login
      navigateToLoginRequestUrl: false,
    },
    cache: {
      cacheLocation: BrowserCacheLocation.LocalStorage,
      storeAuthStateInCookie: true,
    },
    system: {
      loggerOptions: {
        logLevel: environment.production ? LogLevel.Error : LogLevel.Warning,
        piiLoggingEnabled: false,
      },
    },
  });
}

export function msalGuardConfigFactory(): MsalGuardConfiguration {
  return {
    interactionType: InteractionType.Redirect,
    authRequest: { scopes: environment.apiScopes },
    loginFailedRoute: '/login',
  };
}

export const msalProviders = [
  { provide: MSAL_INSTANCE, useFactory: msalInstanceFactory },
  { provide: MSAL_GUARD_CONFIG, useFactory: msalGuardConfigFactory },
  // Interceptor propio: agrega el token solo cuando hay sesión activa,
  // sin lanzar loginRedirect() automáticamente
  { provide: HTTP_INTERCEPTORS, useClass: AzureAuthInterceptor, multi: true },
  MsalService,
  MsalGuard,
  MsalBroadcastService,
];
