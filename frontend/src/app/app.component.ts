import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { MsalBroadcastService } from '@azure/msal-angular';
import { EventMessage, EventType } from '@azure/msal-browser';
import { filter } from 'rxjs';
import { NavigationComponent } from './features/navigation/navigation.component';
import { SidebarComponent } from './features/sidebar/sidebar.component';
import { ComposerComponent } from './features/composer/composer.component';
import { AuthService } from './core/auth/auth.service';

/** Routes that should render without topbar / sidebar (full-page layouts) */
const FULL_PAGE_ROUTES = ['/login', '/auth/finish'];

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NavigationComponent, SidebarComponent, ComposerComponent],
  template: `
    @if (isFullPage()) {
      <!-- Full-page routes: login, auth callback -->
      <router-outlet />
    } @else {
      <div class="app-shell">
        <app-navigation />
        <div class="app-body">
          <aside class="app-sidebar">
            <app-sidebar />
          </aside>
          <main class="app-main">
            <router-outlet />
          </main>
        </div>
      </div>
      <app-composer />
    }
  `,
})
export class AppComponent implements OnInit {
  private auth = inject(AuthService);
  private router = inject(Router);
  private msalBroadcast = inject(MsalBroadcastService, { optional: true });

  readonly isFullPage = signal(false);

  ngOnInit() {
    // Update full-page state on every navigation
    this.router.events
      .pipe(filter(e => e instanceof NavigationEnd))
      .subscribe((e) => {
        const url = (e as NavigationEnd).urlAfterRedirects.split('?')[0];
        this.isFullPage.set(FULL_PAGE_ROUTES.includes(url));
      });

    // Set initial state for the first load
    const initial = this.router.url.split('?')[0];
    this.isFullPage.set(FULL_PAGE_ROUTES.includes(initial));

    this.msalBroadcast?.msalSubject$
      .pipe(filter((msg: EventMessage) => msg.eventType === EventType.LOGIN_SUCCESS))
      .subscribe(() => this.auth.loadCurrentUser());
  }
}
