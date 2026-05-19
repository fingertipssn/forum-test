import { Component, inject, signal, computed, effect } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ComposerStateService } from './composer-state.service';
import { TopicService } from '../../core/services/topic.service';
import { PostService } from '../../core/services/post.service';
import { AuthService } from '../../core/auth/auth.service';
import { CategoryService } from '../../core/services/category.service';
import { UploadService } from '../../core/services/upload.service';
import { MarkdownPipe } from '../../shared/pipes/markdown.pipe';
import type { Category } from '../../core/models/index';

@Component({
  selector: 'app-composer',
  standalone: true,
  imports: [FormsModule, RouterLink, MarkdownPipe],
  templateUrl: './composer.component.html',
  styleUrl: './composer.component.scss',
})
export class ComposerComponent {
  composerState = inject(ComposerStateService);
  private topicService = inject(TopicService);
  private postService = inject(PostService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private categoryService = inject(CategoryService);
  private uploadService = inject(UploadService);

  title = signal('');
  body = signal('');
  submitting = signal(false);
  error = signal<string | null>(null);
  categories = signal<Category[]>([]);
  loadingCategories = signal(false);
  selectedCategoryId = signal<number | null>(null);

  /** Estado de la subida de imagen: idle | uploading | error */
  uploadState = signal<'idle' | 'uploading' | 'error'>('idle');
  uploadError = signal<string | null>(null);

  state = this.composerState.state;
  isNewTopic = computed(() => this.state().mode === 'new_topic');

  constructor() {
    effect(() => {
      const isOpen = this.state().open;
      if (isOpen && this.isNewTopic()) {
        this.loadCategories();
      }
    });
  }

  private loadCategories() {
    this.loadingCategories.set(true);
    this.categoryService.getAll().subscribe({
      next: (res) => {
        this.categories.set(res.categories);
        this.loadingCategories.set(false);
        const stateCategory = this.state().categoryId;
        if (stateCategory) {
          this.selectedCategoryId.set(stateCategory);
        } else if (res.categories.length > 0) {
          this.selectedCategoryId.set(res.categories[0].id);
        }
      },
      error: () => this.loadingCategories.set(false),
    });
  }

  // ── Paste de imagen ────────────────────────────────────────────────────────

  /** El textarea llama a este handler — obtenemos el elemento desde event.target */
  onPaste(event: ClipboardEvent) {
    const items = event.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file' && item.type.startsWith('image/')) {
        event.preventDefault();
        const file = item.getAsFile();
        if (file) this.uploadAndInsert(file, event.target as HTMLTextAreaElement);
        return;
      }
    }
  }

  /** Sube el archivo y reemplaza el placeholder con el markdown definitivo */
  private uploadAndInsert(file: File, textarea: HTMLTextAreaElement | null) {
    this.uploadState.set('uploading');
    this.uploadError.set(null);

    const placeholder = `![subiendo…]()`;
    if (textarea) this.insertAtCursor(textarea, placeholder);

    this.uploadService.uploadImage(file).subscribe({
      next: (result) => {
        const md = `![imagen](${result.url})`;
        this.body.update(b => b.replace(placeholder, md));
        this.uploadState.set('idle');
      },
      error: (err) => {
        this.body.update(b => b.replace(placeholder, ''));
        this.uploadState.set('error');
        this.uploadError.set(
          err?.error?.detail || 'Error al subir la imagen (máx. 10 MB, formatos: jpg, png, gif, webp).'
        );
        setTimeout(() => this.uploadState.set('idle'), 4000);
      },
    });
  }

  /** Inserta texto en la posición actual del cursor */
  private insertAtCursor(textarea: HTMLTextAreaElement, text: string) {
    const start = textarea.selectionStart ?? this.body().length;
    const end   = textarea.selectionEnd   ?? start;
    const current = this.body();
    this.body.set(current.slice(0, start) + text + current.slice(end));
    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + text.length;
      textarea.focus();
    });
  }

  // ── Drag & Drop ────────────────────────────────────────────────────────────

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
  }

  /** El drop puede ser sobre el textarea o sobre el wrapper — buscamos el textarea */
  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    const file = event.dataTransfer?.files[0];
    if (!file || !file.type.startsWith('image/')) return;

    // Busca el textarea dentro del contenedor donde se hizo drop
    const target = event.currentTarget as HTMLElement;
    const textarea = target.querySelector('textarea') as HTMLTextAreaElement | null;
    this.uploadAndInsert(file, textarea);
  }

  // ── Submit ─────────────────────────────────────────────────────────────────

  submit() {
    if (!this.auth.isAuthenticated()) { this.auth.login(); return; }
    this.error.set(null);
    if (this.isNewTopic()) { this.createTopic(); } else { this.createReply(); }
  }

  private createTopic() {
    const titleVal = this.title().trim();
    const bodyVal = this.body().trim();
    if (!titleVal || titleVal.length < 15) {
      this.error.set('El título debe tener al menos 15 caracteres'); return;
    }
    if (!bodyVal) { this.error.set('El contenido no puede estar vacío'); return; }

    this.submitting.set(true);
    this.topicService.create({
      title: titleVal,
      raw: bodyVal,
      categoryId: this.selectedCategoryId() ?? this.state().categoryId,
    }).subscribe({
      next: (topic) => { this.composerState.close(); this.reset(); this.router.navigate(['/t', topic.id]); },
      error: (err) => { this.error.set(err?.error?.detail?.[0]?.msg || err?.error?.detail || 'Error al crear el tema'); this.submitting.set(false); },
    });
  }

  private createReply() {
    const bodyVal = this.body().trim();
    if (!bodyVal) { this.error.set('El contenido no puede estar vacío'); return; }
    const s = this.state();
    this.submitting.set(true);
    this.postService.create({ topicId: s.topicId!, raw: bodyVal, replyToPostNumber: s.replyToPostNumber }).subscribe({
      next: () => { this.composerState.close(); this.reset(); window.location.reload(); },
      error: (err) => { this.error.set(err?.error?.detail?.[0]?.msg || err?.error?.detail || 'Error al enviar la respuesta'); this.submitting.set(false); },
    });
  }

  private reset() {
    this.title.set(''); this.body.set('');
    this.submitting.set(false);
  }

  close() { this.composerState.close(); }
}
