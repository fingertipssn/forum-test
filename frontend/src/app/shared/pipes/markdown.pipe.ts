import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
// eslint-disable-next-line @typescript-eslint/no-require-imports
const DOMPurify = require('dompurify');

marked.setOptions({ breaks: true });

const PURIFY_OPTIONS = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's', 'del', 'ins',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
    'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'hr', 'aside', 'div', 'span',
  ],
  ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'target', 'rel'],
  ALLOW_DATA_ATTR: false,
};

@Pipe({ name: 'markdown', standalone: true })
export class MarkdownPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml {
    if (!value?.trim()) return '';
    const raw = marked.parse(value) as string;
    // DOMPurify sanitizes before we bypass Angular's security check.
    const safe: string = DOMPurify.sanitize(raw, PURIFY_OPTIONS);
    return this.sanitizer.bypassSecurityTrustHtml(safe);
  }
}
