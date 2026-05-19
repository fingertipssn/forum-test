import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { Subscription } from 'rxjs';
import { TopicService } from '../../core/services/topic.service';
import { CategoryService } from '../../core/services/category.service';
import { ComposerStateService } from '../composer/composer-state.service';
import { AuthService } from '../../core/auth/auth.service';
import { TimeAgoPipe } from '../../shared/pipes/time-ago.pipe';
import type { Topic, Category } from '../../core/models/index';

@Component({
  selector: 'app-topic-list',
  standalone: true,
  imports: [RouterLink, TimeAgoPipe, DecimalPipe],
  templateUrl: './topic-list.component.html',
  styleUrl: './topic-list.component.scss',
})
export class TopicListComponent implements OnInit, OnDestroy {
  private topicService = inject(TopicService);
  private categoryService = inject(CategoryService);
  private route = inject(ActivatedRoute);
  composer = inject(ComposerStateService);
  auth = inject(AuthService);

  topics = signal<Topic[]>([]);
  category = signal<Category | null>(null);
  allCategories = this.categoryService.categories;
  loading = signal(true);
  error = signal<string | null>(null);
  page = signal(1);
  total = signal(0);
  perPage = signal(30);

  /** Signal reactivo al slug actual — se actualiza con cada cambio de ruta */
  categorySlug = signal<string>('');

  totalPages = computed(() => Math.ceil(this.total() / this.perPage()));

  private routeSub!: Subscription;

  ngOnInit() {
    // Suscripción al observable de params — se dispara en CADA cambio de ruta
    this.routeSub = this.route.paramMap.subscribe(params => {
      const slug = params.get('slug') ?? '';
      this.categorySlug.set(slug);
      this.category.set(null);   // limpia la categoría anterior
      this.page.set(1);          // vuelve a la página 1
      this.load();
    });

    // Carga inicial del listado de categorías para el panel derecho
    this.categoryService.getAll().subscribe({ error: () => {} });
  }

  ngOnDestroy() {
    this.routeSub?.unsubscribe();
  }

  load() {
    this.loading.set(true);
    this.error.set(null);
    const slug = this.categorySlug();

    if (slug) {
      this.categoryService.getBySlug(slug).subscribe({
        next: (cat) => this.category.set(cat),
        error: () => {},
      });
      this.topicService.getByCategory(slug, this.page()).subscribe({
        next: (res) => {
          this.topics.set(res.topics);
          this.total.set(res.total);
          this.perPage.set(res.perPage);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('Error al cargar los temas.');
          this.loading.set(false);
        },
      });
    } else {
      this.topicService.getLatest(this.page()).subscribe({
        next: (res) => {
          this.topics.set(res.topics);
          this.total.set(res.total);
          this.perPage.set(res.perPage);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('Error al cargar los temas.');
          this.loading.set(false);
        },
      });
    }
  }

  goToPage(p: number) {
    this.page.set(p);
    this.load();
    window.scrollTo(0, 0);
  }

  pageNumbers(): number[] {
    return Array.from({ length: this.totalPages() }, (_, i) => i + 1);
  }

  openNewTopic() {
    const cat = this.category();
    this.composer.openNewTopic(cat?.id);
  }
}
