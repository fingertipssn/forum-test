import { Component, inject, signal, OnDestroy } from '@angular/core';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, switchMap, of } from 'rxjs';
import { AuthService } from '../../core/auth/auth.service';
import { ComposerStateService } from '../composer/composer-state.service';
import { SearchService } from '../../core/services/search.service';
import type { SearchResult } from '../../core/models/index';

@Component({
  selector: 'app-navigation',
  standalone: true,
  imports: [RouterLink, FormsModule],
  templateUrl: './navigation.component.html',
  styleUrl: './navigation.component.scss',
})
export class NavigationComponent implements OnDestroy {
  auth = inject(AuthService);
  composer = inject(ComposerStateService);
  private router = inject(Router);
  private searchService = inject(SearchService);

  searchQuery = signal('');
  menuOpen = signal(false);

  /** Resultados del dropdown */
  dropdownResults = signal<SearchResult[]>([]);
  dropdownOpen = signal(false);
  searching = signal(false);

  /** Pipeline reactivo: debounce 300ms → petición al API */
  private input$ = new Subject<string>();
  private searchSub = this.input$.pipe(
    debounceTime(300),
    distinctUntilChanged(),
    switchMap(q => {
      const trimmed = q.trim();
      if (trimmed.length < 2) {
        this.dropdownResults.set([]);
        this.dropdownOpen.set(false);
        this.searching.set(false);
        return of(null);
      }
      this.searching.set(true);
      return this.searchService.search(trimmed, 1);
    }),
  ).subscribe(res => {
    if (res !== null) {
      this.dropdownResults.set(res.results.slice(0, 6));
      this.dropdownOpen.set(res.results.length > 0);
    }
    this.searching.set(false);
  });

  /** Llamado en cada pulsación de tecla */
  onInput(value: string) {
    this.searchQuery.set(value);
    if (!value.trim()) {
      this.closeDropdown();
    }
    this.input$.next(value);
  }

  /** Enter → página de resultados completa */
  onSearch(event: Event) {
    event.preventDefault();
    const q = this.searchQuery().trim();
    if (q) {
      this.closeDropdown();
      this.router.navigate(['/search'], { queryParams: { q } });
    }
  }

  /** Click en un resultado → navega al tema */
  selectResult(topicId: number) {
    this.closeDropdown();
    this.searchQuery.set('');
    this.router.navigate(['/t', topicId]);
  }

  /** Limpia la búsqueda */
  clearSearch() {
    this.searchQuery.set('');
    this.closeDropdown();
  }

  closeDropdown() {
    this.dropdownOpen.set(false);
    this.dropdownResults.set([]);
  }

  openNewTopic() {
    this.composer.openNewTopic();
  }

  toggleMenu() {
    this.menuOpen.update(v => !v);
  }

  logout() {
    this.auth.logout();
  }

  ngOnDestroy() {
    this.searchSub.unsubscribe();
  }
}
