import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import type { SearchResponse } from '../models/index';

@Injectable({ providedIn: 'root' })
export class SearchService {
  private api = inject(ApiService);

  search(query: string, page = 1): Observable<SearchResponse> {
    return this.api.get<SearchResponse>('/search', { q: query, page });
  }

  reindex(): Observable<{ status: string; posts_indexed: number; topics_indexed: number }> {
    return this.api.post('/search/reindex', {});
  }
}
