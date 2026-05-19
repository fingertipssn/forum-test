import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { environment } from '../../../environments/environment';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  // ── get ───────────────────────────────────────────────────────────────────

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('get() should make a GET request to the correct URL', () => {
    service.get('/categories').subscribe();
    const req = httpMock.expectOne(`${base}/categories`);
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('get() should pass query params', () => {
    service.get('/topics', { page: 1, per_page: 20 }).subscribe();
    const req = httpMock.expectOne(r => r.url === `${base}/topics`);
    expect(req.request.params.get('page')).toBe('1');
    expect(req.request.params.get('per_page')).toBe('20');
    req.flush({});
  });

  it('get() should work without params', () => {
    service.get('/health').subscribe();
    const req = httpMock.expectOne(`${base}/health`);
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'ok' });
  });

  // ── post ──────────────────────────────────────────────────────────────────

  it('post() should make a POST request with body', () => {
    const body = { title: 'Test', raw: 'Content' };
    service.post('/topics', body).subscribe();
    const req = httpMock.expectOne(`${base}/topics`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(body);
    req.flush({ id: 1 });
  });

  // ── put ───────────────────────────────────────────────────────────────────

  it('put() should make a PUT request', () => {
    const body = { name: 'New Name' };
    service.put('/u/alice', body).subscribe();
    const req = httpMock.expectOne(`${base}/u/alice`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(body);
    req.flush({});
  });

  // ── delete ────────────────────────────────────────────────────────────────

  it('delete() should make a DELETE request', () => {
    service.delete('/posts/42').subscribe();
    const req = httpMock.expectOne(`${base}/posts/42`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  // ── postForm ──────────────────────────────────────────────────────────────

  it('postForm() should make a POST request with FormData', () => {
    const fd = new FormData();
    fd.append('file', new Blob(['data'], { type: 'image/jpeg' }), 'avatar.jpg');
    service.postForm('/u/alice/avatar', fd).subscribe();
    const req = httpMock.expectOne(`${base}/u/alice/avatar`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toBeInstanceOf(FormData);
    req.flush({ avatarUrl: 'https://example.com/photo.jpg' });
  });

  // ── error propagation ─────────────────────────────────────────────────────

  it('get() should propagate HTTP errors', (done) => {
    service.get('/missing').subscribe({
      error: (err) => {
        expect(err.status).toBe(404);
        done();
      },
    });
    const req = httpMock.expectOne(`${base}/missing`);
    req.flush('Not Found', { status: 404, statusText: 'Not Found' });
  });
});
