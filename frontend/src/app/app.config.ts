import { ApplicationConfig, APP_INITIALIZER } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi, HTTP_INTERCEPTORS } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { routes } from './app.routes';
import { AuthService } from './core/auth/auth.service';
import { environment } from '../environments/environment';
import { DevAuthInterceptor } from './core/auth/dev-auth.interceptor';
import { msalProviders } from './core/auth/msal.config';

function initializeAuth(auth: AuthService) {
  return () => auth.initialize();
}

const authProviders = environment.devMode
  ? [{ provide: HTTP_INTERCEPTORS, useClass: DevAuthInterceptor, multi: true }]
  : msalProviders;

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptorsFromDi()),
    provideAnimations(),
    ...authProviders,
    {
      provide: APP_INITIALIZER,
      useFactory: initializeAuth,
      deps: [AuthService],
      multi: true,
    },
  ],
};
