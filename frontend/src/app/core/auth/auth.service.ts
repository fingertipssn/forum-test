import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { MsalService, MsalBroadcastService } from '@azure/msal-angular';
import { InteractionStatus } from '@azure/msal-browser';
import { filter, firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DEV_TOKEN_KEY } from './dev-auth.interceptor';
import type { User } from '../models/index';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private msal = inject(MsalService, { optional: true });
  private msalBroadcast = inject(MsalBroadcastService, { optional: true });

  private http = inject(HttpClient);
  private router = inject(Router);

  readonly currentUser = signal<User | null>(null);
  readonly isLoading = signal(true);

  readonly isAuthenticated = computed(() => this.currentUser() !== null);
  readonly isStaff = computed(() => {
    const u = this.currentUser();
    return u ? u.admin || u.moderator : false;
  });

  async initialize(): Promise<void> {
    if (environment.devMode) {
      // ── Modo desarrollo: token JWT local ──
      const token = localStorage.getItem(DEV_TOKEN_KEY);
      if (token) await this.loadCurrentUser();
      this.isLoading.set(false);
      return;
    }

    if (!this.msal || !this.msalBroadcast) {
      this.isLoading.set(false);
      return;
    }

    // ── Azure AD real ──
    await this.msal.instance.initialize();

    // Procesar el redirect de vuelta desde Azure AD
    const redirectResult = await this.msal.instance.handleRedirectPromise().catch(err => {
      console.error('[Auth] handleRedirectPromise error:', err);
      return null;
    });

    console.log('[Auth] redirectResult:', redirectResult
      ? `account=${redirectResult.account?.username}, hasToken=${!!redirectResult.accessToken}`
      : 'null');

    if (redirectResult?.account) {
      this.msal.instance.setActiveAccount(redirectResult.account);
      console.log('[Auth] Redirect login OK — cargando usuario con token directo');
      await this.loadCurrentUser(redirectResult.accessToken || undefined);
      console.log('[Auth] currentUser después de redirect:', this.currentUser());
      await this.router.navigate(['/latest']);
      this.isLoading.set(false);
      return;
    }

    // Esperar a que MSAL termine cualquier interacción en curso
    await firstValueFrom(
      this.msalBroadcast.inProgress$.pipe(
        filter((s) => s === InteractionStatus.None)
      )
    );

    // Si ya había una sesión activa (ej. recarga de página)
    const accounts = this.msal.instance.getAllAccounts();
    console.log('[Auth] Cuentas en caché:', accounts.length);
    if (accounts.length > 0) {
      this.msal.instance.setActiveAccount(accounts[0]);
      await this.loadCurrentUser();
      console.log('[Auth] currentUser después de sesión existente:', this.currentUser());
    }

    this.isLoading.set(false);
  }

  async login(): Promise<void> {
    if (environment.devMode) {
      await this.router.navigate(['/login']);
      return;
    }
    if (this.msal) {
      await this.msal.instance.loginRedirect({
        scopes: environment.apiScopes,
        prompt: 'select_account',
      });
    }
  }

  async logout(): Promise<void> {
    this.currentUser.set(null);
    if (environment.devMode) {
      localStorage.removeItem(DEV_TOKEN_KEY);
      await this.router.navigate(['/login']);
      return;
    }
    if (this.msal) {
      await this.msal.instance.logoutRedirect({
        postLogoutRedirectUri: environment.msalConfig.auth.postLogoutRedirectUri,
      });
    }
  }

  /**
   * Carga el usuario autenticado desde el backend.
   * @param bearerToken Token de acceso opcional. Si se pasa, se adjunta directamente
   *   como header Authorization para evitar la adquisición silenciosa del interceptor
   *   (útil justo después de handleRedirectPromise cuando MSAL aún está estabilizando).
   */
  async loadCurrentUser(bearerToken?: string): Promise<void> {
    try {
      const options = bearerToken
        ? { headers: { Authorization: `Bearer ${bearerToken}` } }
        : {};
      const user = await firstValueFrom(
        this.http.get<User>(`${environment.apiUrl}/auth/me`, options)
      );
      this.currentUser.set(user);
    } catch (err: any) {
      console.error('[Auth] loadCurrentUser error:', err?.status, err?.error ?? err?.message ?? err);
      if (environment.devMode) {
        localStorage.removeItem(DEV_TOKEN_KEY);
      }
      this.currentUser.set(null);
    }
  }

  // Solo para devMode
  async devLogin(username: string, email: string, name: string): Promise<void> {
    const resp = await firstValueFrom(
      this.http.post<{ access_token: string; user: User }>(
        `${environment.apiUrl}/auth/dev-login`,
        { username, email, name }
      )
    );
    localStorage.setItem(DEV_TOKEN_KEY, resp.access_token);
    this.currentUser.set(resp.user);
    await this.router.navigate(['/latest']);
  }
}
