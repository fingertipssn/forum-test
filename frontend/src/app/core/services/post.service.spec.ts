import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { PostService } from './post.service';
import { ApiService } from './api.service';
import { environment } from '../../../environments/environment';

describe('PostService', () => {
  let service: PostService;
  let httpMock: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [PostService, ApiService],
    });
    service = TestBed.inject(PostService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // ── create ────────────────────────────────────────────────────────────────

  it('create() should POST to /posts with snake_case body', () => {
    service.create({ topicId: 5, raw: 'Hello!' }).subscribe();
    const req = httpMock.expectOne(`${base}/posts`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body['topic_id']).toBe(5);
    expect(req.request.body['raw']).toBe('Hello!');
    req.flush({ id: 1 });
  });

  it('create() should include reply_to_post_number when provided', () => {
    service.create({ topicId: 5, raw: 'Reply', replyToPostNumber: 3 }).subscribe();
    const req = httpMock.expectOne(`${base}/posts`);
    expect(req.request.body['reply_to_post_number']).toBe(3);
    req.flush({ id: 2 });
  });

  it('create() should send null for reply_to_post_number when omitted', () => {
    service.create({ topicId: 5, raw: 'No reply' }).subscribe();
    const req = httpMock.expectOne(`${base}/posts`);
    expect(req.request.body['reply_to_post_number']).toBeNull();
    req.flush({ id: 3 });
  });

  // ── update ────────────────────────────────────────────────────────────────

  it('update() should PUT to /posts/:id', () => {
    service.update(7, { raw: 'Updated content' }).subscribe();
    const req = httpMock.expectOne(`${base}/posts/7`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body['raw']).toBe('Updated content');
    req.flush({ id: 7 });
  });

  it('update() should include edit_reason when provided', () => {
    service.update(7, { raw: 'Fixed', editReason: 'typo' }).subscribe();
    const req = httpMock.expectOne(`${base}/posts/7`);
    expect(req.request.body['edit_reason']).toBe('typo');
    req.flush({ id: 7 });
  });

  // ── delete ────────────────────────────────────────────────────────────────

  it('delete() should DELETE to /posts/:id', () => {
    service.delete(42).subscribe();
    const req = httpMock.expectOne(`${base}/posts/42`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  // ── like ──────────────────────────────────────────────────────────────────

  it('like() should POST to /posts/:id/like', () => {
    service.like(10).subscribe((res) => {
      expect(res.liked).toBeTrue();
      expect(res.likeCount).toBe(5);
    });
    const req = httpMock.expectOne(`${base}/posts/10/like`);
    expect(req.request.method).toBe('POST');
    req.flush({ liked: true, likeCount: 5 });
  });

  it('like() can return liked=false (toggle off)', () => {
    service.like(10).subscribe((res) => {
      expect(res.liked).toBeFalse();
    });
    const req = httpMock.expectOne(`${base}/posts/10/like`);
    req.flush({ liked: false, likeCount: 4 });
  });

  // ── bookmark ──────────────────────────────────────────────────────────────

  it('bookmark() should POST to /posts/:id/bookmark', () => {
    service.bookmark(3).subscribe((res) => {
      expect(res.bookmarked).toBeTrue();
    });
    const req = httpMock.expectOne(`${base}/posts/3/bookmark`);
    expect(req.request.method).toBe('POST');
    req.flush({ bookmarked: true });
  });

  it('bookmark() can return bookmarked=false (toggle off)', () => {
    service.bookmark(3).subscribe((res) => {
      expect(res.bookmarked).toBeFalse();
    });
    const req = httpMock.expectOne(`${base}/posts/3/bookmark`);
    req.flush({ bookmarked: false });
  });
});
