import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  auth = inject(AuthService);
  private router = inject(Router);

  readonly devMode = environment.devMode;

  username = '';
  email = '';
  name = '';
  loading = signal(false);
  error = signal('');

  login() {
    this.auth.login();
  }

  async devSubmit() {
    const u = this.username.trim();
    if (!u) {
      this.error.set('El nombre de usuario es obligatorio.');
      return;
    }
    this.error.set('');
    this.loading.set(true);
    try {
      await this.auth.devLogin(u, this.email.trim(), this.name.trim());
    } catch (err: any) {
      const msg = err?.error?.detail ?? 'Error al iniciar sesión. Inténtalo de nuevo.';
      this.error.set(msg);
    } finally {
      this.loading.set(false);
    }
  }
}
