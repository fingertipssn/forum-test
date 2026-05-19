import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CategoryService } from '../../core/services/category.service';
import { ComposerStateService } from '../composer/composer-state.service';
import { AuthService } from '../../core/auth/auth.service';
import type { Category } from '../../core/models/index';

@Component({
  selector: 'app-category-list',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './category-list.component.html',
  styleUrl: './category-list.component.scss',
})
export class CategoryListComponent implements OnInit {
  private categoryService = inject(CategoryService);
  composer = inject(ComposerStateService);
  auth = inject(AuthService);

  categories = signal<Category[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  ngOnInit() {
    this.categoryService.getAll().subscribe({
      next: (res) => {
        this.categories.set(res.categories);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar las categorías.');
        this.loading.set(false);
      },
    });
  }

  openNewTopic(categoryId: number) {
    this.composer.openNewTopic(categoryId);
  }

  trackById(_: number, cat: Category) {
    return cat.id;
  }
}
