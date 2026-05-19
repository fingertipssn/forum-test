import { Component, inject, signal, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CategoryService } from '../../core/services/category.service';
import type { Category } from '../../core/models/index';

@Component({
  selector: 'app-admin-categories',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './admin-categories.component.html',
  styleUrl: './admin-categories.component.scss',
})
export class AdminCategoriesComponent implements OnInit {
  private categoryService = inject(CategoryService);

  /** Signal global — incluye las categorías recién creadas sin refetch */
  categories = this.categoryService.categories;
  loading = signal(true);
  saving = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);

  // Formulario nueva categoría
  newName = signal('');
  newDescription = signal('');
  newColor = signal('#0088CC');
  newTextColor = signal('#FFFFFF');

  ngOnInit() {
    this.loadCategories();
  }

  loadCategories() {
    this.loading.set(true);
    // getAll() ya actualiza el signal global via tap; aquí solo manejamos loading/error
    this.categoryService.getAll().subscribe({
      next: () => this.loading.set(false),
      error: () => {
        this.error.set('Error al cargar categorías');
        this.loading.set(false);
      },
    });
  }

  /** Convierte "#RRGGBB" → "RRGGBB" para enviar al backend */
  private hexToCode(hex: string): string {
    return hex.replace('#', '').toUpperCase();
  }

  createCategory() {
    const name = this.newName().trim();
    if (!name) {
      this.error.set('El nombre es obligatorio');
      return;
    }

    this.saving.set(true);
    this.error.set(null);
    this.success.set(null);

    this.categoryService.create({
      name,
      description: this.newDescription().trim() || undefined,
      color: this.hexToCode(this.newColor()),
      textColor: this.hexToCode(this.newTextColor()),
    }).subscribe({
      next: (cat) => {
        // El tap en CategoryService.create() ya añade la categoría al signal global
        this.newName.set('');
        this.newDescription.set('');
        this.newColor.set('#0088CC');
        this.newTextColor.set('#FFFFFF');
        this.saving.set(false);
        this.success.set(`Categoría "${cat.name}" creada correctamente`);
        setTimeout(() => this.success.set(null), 3000);
      },
      error: (err) => {
        this.error.set(
          err?.error?.detail?.[0]?.msg ||
          err?.error?.detail ||
          'Error al crear la categoría'
        );
        this.saving.set(false);
      },
    });
  }

  categoryBadgeStyle(cat: Category): string {
    return `background:#${cat.color};color:#${cat.textColor}`;
  }
}
