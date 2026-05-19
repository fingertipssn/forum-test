import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';

// Configurar marked una sola vez: no escapa HTML para que las imágenes funcionen
marked.setOptions({ breaks: true });

@Pipe({ name: 'markdown', standalone: true })
export class MarkdownPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml {
    if (!value?.trim()) return '';
    // marked.parse() es síncrono cuando no hay extensiones async
    const html = marked.parse(value) as string;
    // bypassSecurityTrustHtml: confiamos en el HTML generado por marked
    // (en producción añadir DOMPurify para sanitización adicional)
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
