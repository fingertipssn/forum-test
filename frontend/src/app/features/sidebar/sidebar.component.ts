import { Component, inject, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CategoryService } from '../../core/services/category.service';
import { AuthService } from '../../core/auth/auth.service';
import { ComposerStateService } from '../composer/composer-state.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent implements OnInit {
  private categoryService = inject(CategoryService);
  auth = inject(AuthService);
  private composer = inject(ComposerStateService);

  /** Lee el signal global — se actualiza automáticamente cuando se crea una categoría */
  categories = this.categoryService.categories;

  ngOnInit() {
    // Carga inicial (actualiza el signal global; otros componentes se benefician también)
    this.categoryService.getAll().subscribe({ error: () => {} });
  }

  openNewTopic() {
    this.composer.openNewTopic();
  }
}
