import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { ApiService } from './api.service';
import type { CategoryListResponse, Category } from '../models/index';

export interface CategoryCreatePayload {
  name: string;
  description?: string;
  color?: string;
  textColor?: string;
}

@Injectable({ providedIn: 'root' })
export class CategoryService {
  private api = inject(ApiService);

  /** Estado global compartido — cualquier componente puede leerlo sin hacer fetch */
  readonly categories = signal<Category[]>([]);

  getAll(): Observable<CategoryListResponse> {
    return this.api.get<CategoryListResponse>('/categories').pipe(
      tap(res => this.categories.set(res.categories)),
    );
  }

  getBySlug(slug: string): Observable<Category> {
    return this.api.get<Category>(`/categories/${slug}`);
  }

  create(payload: CategoryCreatePayload): Observable<Category> {
    return this.api.post<Category>('/categories', payload).pipe(
      // Añade la nueva categoría al estado global sin necesidad de otro fetch
      tap(cat => this.categories.update(list => [...list, cat])),
    );
  }
}
