import { Injectable, inject } from '@angular/core';
import {
  HttpRequest, HttpHandler, HttpEvent, HttpInterceptor,
} from '@angular/common/http';
import { Observable, from, switchMap, catchError } from 'rxjs';
import { MsalService } from '@azure/msal-angular';
import { environment } from '../../../environments/environment';

/**
 * Interceptor que agrega el Bearer token de Azure AD solo cuando el usuario
 * ya tiene una sesión activa. NO lanza loginRedirect() automáticamente,
 * lo que permite que rutas públicas funcionen sin autenticación.
 */
@Injectable()
export class AzureAuthInterceptor implements HttpInterceptor {
  private msal = inject(MsalService, { optional: true });

  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // Solo interceptar peticiones al API del foro
    if (!req.url.startsWith(environment.apiUrl)) {
      return next.handle(req);
    }

    // Si la petición ya lleva un Authorization header (pasado manualmente, p.ej.
    // justo después del redirect con el token del redirectResult), no sobreescribir.
    if (req.headers.has('Authorization')) {
      return next.handle(req);
    }

    const account = this.msal?.instance.getActiveAccount()
                 ?? this.msal?.instance.getAllAccounts()[0];

    // Sin sesión activa → pasar la petición sin token (el backend responde 401 si es necesario)
    if (!account || !this.msal) {
      return next.handle(req);
    }

    // Con sesión activa → adquirir token silenciosamente y adjuntarlo
    return from(
      this.msal.instance.acquireTokenSilent({
        scopes: environment.apiScopes,
        account,
      })
    ).pipe(
      switchMap(result => {
        const authReq = req.clone({
          setHeaders: { Authorization: `Bearer ${result.accessToken}` },
        });
        return next.handle(authReq);
      }),
      catchError((err) => {
        // Si falla la adquisición silenciosa (token expirado, etc.)
        // pasar sin token y dejar que el componente maneje el 401
        console.warn('[AzureAuthInterceptor] acquireTokenSilent falló:', err?.errorCode ?? err);
        return next.handle(req);
      }),
    );
  }
}
