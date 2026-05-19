import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import type { TopicListResponse, TopicWithPosts, Topic } from '../models/index';

export interface CreateTopicPayload {
  title: string;
  raw: string;
  categoryId?: number;
}

export interface UpdateTopicPayload {
  title?: string;
  categoryId?: number;
}

@Injectable({ providedIn: 'root' })
export class TopicService {
  private api = inject(ApiService);

  getLatest(page = 1): Observable<TopicListResponse> {
    return this.api.get<TopicListResponse>('/topics/latest', { page });
  }

  getByCategory(slug: string, page = 1): Observable<TopicListResponse> {
    return this.api.get<TopicListResponse>(`/c/${slug}/topics`, { page });
  }

  getTopic(id: number, page = 1): Observable<TopicWithPosts> {
    return this.api.get<TopicWithPosts>(`/t/${id}`, { page });
  }

  create(payload: CreateTopicPayload): Observable<Topic> {
    return this.api.post<Topic>('/t', {
      title: payload.title,
      raw: payload.raw,
      category_id: payload.categoryId ?? null,
    });
  }

  update(id: number, payload: UpdateTopicPayload): Observable<Topic> {
    return this.api.put<Topic>(`/t/${id}`, {
      title: payload.title,
      category_id: payload.categoryId,
    });
  }

  delete(id: number): Observable<void> {
    return this.api.delete<void>(`/t/${id}`);
  }
}
