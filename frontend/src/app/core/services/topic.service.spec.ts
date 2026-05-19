import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TopicService } from './topic.service';
import { ApiService } from './api.service';
import { environment } from '../../../environments/environment';

const base = environment.apiUrl;

describe('TopicService', () => {
  let service: TopicService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [TopicService, ApiService],
    });
    service = TestBed.inject(TopicService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // ── getLatest ─────────────────────────────────────────────────────────────

  it('getLatest() should GET /topics/latest with page param', () => {
    service.getLatest(1).subscribe();
    const req = httpMock.expectOne((r) => r.url === `${base}/topics/latest`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('page')).toBe('1');
    req.flush({ topics: [], total: 0, page: 1, perPage: 20 });
  });

  it('getLatest() defaults to page 1', () => {
    service.getLatest().subscribe();
    const req = httpMock.expectOne((r) => r.url === `${base}/topics/latest`);
    expect(req.request.params.get('page')).toBe('1');
    req.flush({ topics: [], total: 0, page: 1, perPage: 20 });
  });

  // ── getByCategory ─────────────────────────────────────────────────────────

  it('getByCategory() should GET /c/:slug/topics', () => {
    service.getByCategory('tech', 2).subscribe();
    const req = httpMock.expectOne((r) => r.url === `${base}/c/tech/topics`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('page')).toBe('2');
    req.flush({ topics: [], total: 0, page: 2, perPage: 20 });
  });

  // ── getTopic ──────────────────────────────────────────────────────────────

  it('getTopic() should GET /t/:id with page param', () => {
    service.getTopic(42, 1).subscribe();
    const req = httpMock.expectOne((r) => r.url === `${base}/t/42`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('page')).toBe('1');
    req.flush({ topic: {}, posts: [], totalPosts: 0, page: 1, perPage: 20 });
  });

  // ── create ────────────────────────────────────────────────────────────────

  it('create() should POST to /t with snake_case payload', () => {
    service.create({ title: 'Hello', raw: 'Content', categoryId: 3 }).subscribe();
    const req = httpMock.expectOne(`${base}/t`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body['title']).toBe('Hello');
    expect(req.request.body['raw']).toBe('Content');
    expect(req.request.body['category_id']).toBe(3);
    req.flush({ id: 1 });
  });

  it('create() should send null for category_id when omitted', () => {
    service.create({ title: 'Hello', raw: 'Content' }).subscribe();
    const req = httpMock.expectOne(`${base}/t`);
    expect(req.request.body['category_id']).toBeNull();
    req.flush({ id: 1 });
  });

  // ── update ────────────────────────────────────────────────────────────────

  it('update() should PUT to /t/:id', () => {
    service.update(5, { title: 'New Title' }).subscribe();
    const req = httpMock.expectOne(`${base}/t/5`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body['title']).toBe('New Title');
    req.flush({ id: 5 });
  });

  // ── delete ────────────────────────────────────────────────────────────────

  it('delete() should DELETE to /t/:id', () => {
    service.delete(7).subscribe();
    const req = httpMock.expectOne(`${base}/t/7`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
