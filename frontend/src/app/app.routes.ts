import { Routes } from '@angular/router';
import { authGuard } from './core/auth/auth.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/category-list/category-list.component').then(
        (m) => m.CategoryListComponent
      ),
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'latest',
    loadComponent: () =>
      import('./features/topic-list/topic-list.component').then(
        (m) => m.TopicListComponent
      ),
  },
  {
    path: 'c/:slug',
    loadComponent: () =>
      import('./features/topic-list/topic-list.component').then(
        (m) => m.TopicListComponent
      ),
  },
  {
    path: 't/:id',
    loadComponent: () =>
      import('./features/topic-detail/topic-detail.component').then(
        (m) => m.TopicDetailComponent
      ),
  },
  {
    path: 't/:slug/:id',
    redirectTo: 't/:id',
  },
  {
    path: 'search',
    loadComponent: () =>
      import('./features/search/search-results.component').then(
        (m) => m.SearchResultsComponent
      ),
  },
  {
    path: 'u/:username',
    loadComponent: () =>
      import('./features/user-profile/user-profile.component').then(
        (m) => m.UserProfileComponent
      ),
  },
  {
    path: 'bookmarks',
    loadComponent: () =>
      import('./features/bookmarks/bookmarks.component').then(
        (m) => m.BookmarksComponent
      ),
  },
  {
    path: 'admin/categories',
    loadComponent: () =>
      import('./features/admin-categories/admin-categories.component').then(
        (m) => m.AdminCategoriesComponent
      ),
  },
  {
    // URI de redirect de Azure AD — MSAL procesa el auth code aquí
    path: 'auth/finish',
    loadComponent: () =>
      import('./features/auth-callback/auth-callback.component').then(
        (m) => m.AuthCallbackComponent
      ),
  },
  { path: '**', redirectTo: '' },
];
