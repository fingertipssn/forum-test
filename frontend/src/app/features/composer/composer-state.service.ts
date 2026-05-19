import { Injectable, signal } from '@angular/core';

export type ComposerMode = 'new_topic' | 'reply';

export interface ComposerState {
  open: boolean;
  mode: ComposerMode;
  topicId?: number;
  topicTitle?: string;
  replyToPostNumber?: number;
  categoryId?: number;
}

@Injectable({ providedIn: 'root' })
export class ComposerStateService {
  state = signal<ComposerState>({ open: false, mode: 'new_topic' });

  openNewTopic(categoryId?: number) {
    this.state.set({ open: true, mode: 'new_topic', categoryId });
  }

  openReply(topicId: number, topicTitle: string, replyToPostNumber?: number) {
    this.state.set({ open: true, mode: 'reply', topicId, topicTitle, replyToPostNumber });
  }

  close() {
    this.state.update((s) => ({ ...s, open: false }));
  }
}
