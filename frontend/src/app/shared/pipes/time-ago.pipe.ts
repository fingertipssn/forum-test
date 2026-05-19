import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'timeAgo', standalone: true, pure: false })
export class TimeAgoPipe implements PipeTransform {
  transform(value: string | Date | null | undefined): string {
    if (!value) return '';
    const date = typeof value === 'string' ? new Date(value) : value;
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);

    if (diffSec < 60) return 'hace un momento';
    if (diffSec < 3600) {
      const m = Math.floor(diffSec / 60);
      return `hace ${m}m`;
    }
    if (diffSec < 86400) {
      const h = Math.floor(diffSec / 3600);
      return `hace ${h}h`;
    }
    if (diffSec < 2592000) {
      const d = Math.floor(diffSec / 86400);
      return `hace ${d}d`;
    }
    if (diffSec < 31536000) {
      const mo = Math.floor(diffSec / 2592000);
      return `hace ${mo} mes${mo > 1 ? 'es' : ''}`;
    }
    const y = Math.floor(diffSec / 31536000);
    return `hace ${y} año${y > 1 ? 's' : ''}`;
  }
}
