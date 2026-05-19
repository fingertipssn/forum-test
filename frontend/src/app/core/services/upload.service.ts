import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface UploadResult {
  id: number;
  url: string;
  original_filename: string;
  filesize: number;
  width: number | null;
  height: number | null;
  extension: string | null;
  thumbnail_width: number | null;
  thumbnail_height: number | null;
}

@Injectable({ providedIn: 'root' })
export class UploadService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  /** Sube una imagen y la registra en la tabla uploads de Discourse. */
  uploadImage(file: File): Observable<UploadResult> {
    const form = new FormData();
    form.append('file', file, file.name || 'paste.png');
    return this.http.post<UploadResult>(`${this.base}/uploads`, form);
  }

  /**
   * Registra la relación entre un upload y un post o tema
   * en la tabla upload_references.
   * targetType: 'Post' | 'Topic'
   */
  createReference(uploadId: number, targetType: 'Post' | 'Topic', targetId: number): Observable<unknown> {
    const params = new HttpParams()
      .set('target_type', targetType)
      .set('target_id', targetId);
    return this.http.post(`${this.base}/uploads/${uploadId}/reference`, null, { params });
  }
}
