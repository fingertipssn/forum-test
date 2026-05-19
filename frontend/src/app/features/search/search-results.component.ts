import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink, ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SearchService } from '../../core/services/search.service';
import { TimeAgoPipe } from '../../shared/pipes/time-ago.pipe';
import type { SearchResult } from '../../core/models/index';

@Component({
  selector: 'app-search-results',
  standalone: true,
  imports: [RouterLink, FormsModule, TimeAgoPipe],
  templateUrl: './search-results.component.html',
  styleUrl: './search-results.component.scss',
})
export class SearchResultsComponent implements OnInit {
  private searchService = inject(SearchService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  query = signal('');
  results = signal<SearchResult[]>([]);
  total = signal(0);
  loading = signal(false);
  error = signal<string | null>(null);
  page = signal(1);

  ngOnInit() {
    this.route.queryParamMap.subscribe((params) => {
      const q = params.get('q') ?? '';
      this.query.set(q);
      this.page.set(1);
      if (q.trim().length >= 2) {
        this.doSearch();
      }
    });
  }

  doSearch() {
    const q = this.query().trim();
    if (q.length < 2) return;
    this.loading.set(true);
    this.error.set(null);
    this.searchService.search(q, this.page()).subscribe({
      next: (res) => {
        this.results.set(res.results);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Error al realizar la búsqueda.');
        this.loading.set(false);
      },
    });
  }

  onSubmit(event: Event) {
    event.preventDefault();
    const q = this.query().trim();
    if (q) {
      this.router.navigate(['/search'], { queryParams: { q } });
    }
  }

  trackById(_: number, r: SearchResult) { return r.topicId; }
}
