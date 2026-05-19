import { Component } from '@angular/core';

/**
 * Componente mínimo que actúa como landing page del redirect URI de Azure AD.
 * MSAL procesa el auth code en AuthService.initialize() (APP_INITIALIZER)
 * antes de que este componente se renderice, por lo que solo necesita mostrar
 * un spinner mientras la inicialización termina y redirige al foro.
 */
@Component({
  selector: 'app-auth-callback',
  standalone: true,
  template: `
    <div style="display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;gap:1rem;">
      <div class="spinner"></div>
      <p style="color:#888;font-size:.9rem;">Completando inicio de sesión…</p>
    </div>
  `,
})
export class AuthCallbackComponent {}
