import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import type { Post } from '../models/index';

export interface CreatePostPayload {
  topicId: number;
  raw: string;
  replyToPostNumber?: number;
}

export interface UpdatePostPayload {
  raw: string;
  editReason?: string;
}

@Injectable({ providedIn: 'root' })
export class PostService {
  private api = inject(ApiService);

  create(payload: CreatePostPayload): Observable<Post> {
    return this.api.post<Post>('/posts', {
      topic_id: payload.topicId,
      raw: payload.raw,
      reply_to_post_number: payload.replyToPostNumber ?? null,
    });
  }

  update(id: number, payload: UpdatePostPayload): Observable<Post> {
    return this.api.put<Post>(`/posts/${id}`, {
      raw: payload.raw,
      edit_reason: payload.editReason,
    });
  }

  delete(id: number): Observable<void> {
    return this.api.delete<void>(`/posts/${id}`);
  }

  like(id: number): Observable<{ liked: boolean; likeCount: number }> {
    return this.api.post<{ liked: boolean; likeCount: number }>(`/posts/${id}/like`, {});
  }

  bookmark(id: number): Observable<{ bookmarked: boolean }> {
    return this.api.post<{ bookmarked: boolean }>(`/posts/${id}/bookmark`, {});
  }
}
