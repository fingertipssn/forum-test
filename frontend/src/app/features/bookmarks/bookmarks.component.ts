import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { TimeAgoPipe } from '../../shared/pipes/time-ago.pipe';

export interface BookmarkItem {
  postId: number;
  postNumber: number;
  topicId: number;
  topicTitle: string;
  topicSlug: string | null;
  categoryId: number | null;
  excerpt: string;
  bookmarkedAt: string;
  authorUsername: string | null;
  authorName: string | null;
  authorAvatarUrl: string | null;
}

@Component({
  selector: 'app-bookmarks',
  standalone: true,
  imports: [RouterLink, TimeAgoPipe],
  templateUrl: './bookmarks.component.html',
  styleUrl: './bookmarks.component.scss',
})
export class BookmarksComponent implements OnInit {
  private api = inject(ApiService);

  bookmarks = signal<BookmarkItem[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);

  ngOnInit() {
    this.api.get<{ bookmarks: BookmarkItem[] }>('/bookmarks').subscribe({
      next: (res) => {
        this.bookmarks.set(res.bookmarks);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar los temas guardados.');
        this.loading.set(false);
      },
    });
  }

  displayName(b: BookmarkItem): string {
    return b.authorName || b.authorUsername || '?';
  }

  hasRealAvatar(b: BookmarkItem): boolean {
    return !!(b.authorAvatarUrl && !b.authorAvatarUrl.includes('letter_avatar'));
  }

  letterFor(b: BookmarkItem): string {
    return (b.authorUsername?.[0] ?? '?').toUpperCase();
  }
}
