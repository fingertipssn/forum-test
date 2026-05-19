import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { TopicService } from '../../core/services/topic.service';
import { PostService } from '../../core/services/post.service';
import { ComposerStateService } from '../composer/composer-state.service';
import { AuthService } from '../../core/auth/auth.service';
import { TimeAgoPipe } from '../../shared/pipes/time-ago.pipe';
import type { TopicDetail, Post } from '../../core/models/index';

@Component({
  selector: 'app-topic-detail',
  standalone: true,
  imports: [RouterLink, TimeAgoPipe],
  templateUrl: './topic-detail.component.html',
  styleUrl: './topic-detail.component.scss',
})
export class TopicDetailComponent implements OnInit {
  private topicService = inject(TopicService);
  private postService = inject(PostService);
  private route = inject(ActivatedRoute);
  composer = inject(ComposerStateService);
  auth = inject(AuthService);

  topic = signal<TopicDetail | null>(null);
  posts = signal<Post[]>([]);
  loading = signal(true);
  error = signal<string | null>(null);
  page = signal(1);
  totalPosts = signal(0);
  perPage = signal(20);
  editingPostId = signal<number | null>(null);
  editRaw = signal('');

  topicId = computed(() => Number(this.route.snapshot.paramMap.get('id')));
  totalPages = computed(() => Math.ceil(this.totalPosts() / this.perPage()));

  ngOnInit() {
    this.load();
  }

  load() {
    this.loading.set(true);
    this.error.set(null);
    this.topicService.getTopic(this.topicId(), this.page()).subscribe({
      next: (res) => {
        this.topic.set(res.topic);
        this.posts.set(res.posts);
        this.totalPosts.set(res.totalPosts);
        this.perPage.set(res.perPage);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el tema.');
        this.loading.set(false);
      },
    });
  }

  goToPage(p: number) {
    this.page.set(p);
    this.load();
    window.scrollTo(0, 0);
  }

  pageNumbers(): number[] {
    return Array.from({ length: this.totalPages() }, (_, i) => i + 1);
  }

  reply() {
    const t = this.topic();
    if (!t) return;
    this.composer.openReply(t.id, t.title);
  }

  replyToPost(post: Post) {
    const t = this.topic();
    if (!t) return;
    this.composer.openReply(t.id, t.title, post.postNumber);
  }

  startEdit(post: Post) {
    this.editingPostId.set(post.id);
    this.editRaw.set(post.raw);
  }

  cancelEdit() {
    this.editingPostId.set(null);
    this.editRaw.set('');
  }

  saveEdit(post: Post) {
    this.postService.update(post.id, { raw: this.editRaw() }).subscribe({
      next: (updated) => {
        this.posts.update((posts) =>
          posts.map((p) => (p.id === updated.id ? updated : p))
        );
        this.cancelEdit();
      },
      error: () => alert('Error al editar el post.'),
    });
  }

  toggleLike(post: Post) {
    if (!this.auth.isAuthenticated()) return;
    this.postService.like(post.id).subscribe({
      next: (res) => {
        this.posts.update((posts) =>
          posts.map((p) =>
            p.id === post.id
              ? { ...p, likedByMe: res.liked, likeCount: res.likeCount }
              : p
          )
        );
      },
      error: () => {},
    });
  }

  toggleBookmark(post: Post) {
    if (!this.auth.isAuthenticated()) return;
    this.postService.bookmark(post.id).subscribe({
      next: (res) => {
        this.posts.update((posts) =>
          posts.map((p) =>
            p.id === post.id ? { ...p, bookmarkedByMe: res.bookmarked } : p
          )
        );
      },
      error: () => {},
    });
  }

  sharePost(post: Post) {
    const url = `${window.location.origin}/t/${post.topicId}#post-${post.postNumber}`;
    navigator.clipboard.writeText(url).then(() => {
      // Visual feedback handled in template via CSS
    });
  }

  trackById(_: number, p: Post) { return p.id; }
}
