import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CategoryService } from './category.service';
import { ApiService } from './api.service';
import { environment } from '../../../environments/environment';

const base = environment.apiUrl;

const MOCK_CATEGORIES = [
  {
    id: 1, name: 'Tech', slug: 'tech', color: '0088CC', textColor: 'FFFFFF',
    description: null, topicCount: 10, postCount: 50,
    parentCategoryId: null, readRestricted: false,
    position: 1, topicTemplate: null, emoji: null, icon: null,
    createdAt: '2024-01-01T00:00:00', latestTopics: [],
  },
  {
    id: 2, name: 'Science', slug: 'science', color: 'FF5733', textColor: 'FFFFFF',
    description: 'Science topics', topicCount: 5, postCount: 20,
    parentCategoryId: null, readRestricted: false,
    position: 2, topicTemplate: null, emoji: null, icon: null,
    createdAt: '2024-01-01T00:00:00', latestTopics: [],
  },
];

describe('CategoryService', () => {
  let service: CategoryService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [CategoryService, ApiService],
    });
    service = TestBed.inject(CategoryService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initialise categories signal as empty array', () => {
    expect(service.categories()).toEqual([]);
  });

  // ── getAll ────────────────────────────────────────────────────────────────

  it('getAll() should GET /categories', () => {
    service.getAll().subscribe();
    const req = httpMock.expectOne(`${base}/categories`);
    expect(req.request.method).toBe('GET');
    req.flush({ categories: MOCK_CATEGORIES });
  });

  it('getAll() should update the categories signal', () => {
    service.getAll().subscribe((res) => {
      expect(res.categories.length).toBe(2);
    });
    const req = httpMock.expectOne(`${base}/categories`);
    req.flush({ categories: MOCK_CATEGORIES });
    // After flush the signal should be updated
    expect(service.categories().length).toBe(2);
    expect(service.categories()[0].name).toBe('Tech');
  });

  // ── getBySlug ─────────────────────────────────────────────────────────────

  it('getBySlug() should GET /categories/:slug', () => {
    service.getBySlug('tech').subscribe();
    const req = httpMock.expectOne(`${base}/categories/tech`);
    expect(req.request.method).toBe('GET');
    req.flush(MOCK_CATEGORIES[0]);
  });

  // ── create ────────────────────────────────────────────────────────────────

  it('create() should POST to /categories', () => {
    service.create({ name: 'NewCat', color: '123456', textColor: 'FFFFFF' }).subscribe();
    const req = httpMock.expectOne(`${base}/categories`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'NewCat', color: '123456', textColor: 'FFFFFF' });
    req.flush({ ...MOCK_CATEGORIES[0], id: 3, name: 'NewCat', slug: 'newcat' });
  });

  it('create() should append the new category to the signal', () => {
    // Seed with initial categories
    service.getAll().subscribe();
    httpMock.expectOne(`${base}/categories`).flush({ categories: [MOCK_CATEGORIES[0]] });
    expect(service.categories().length).toBe(1);

    // Create a second
    service.create({ name: 'NewCat' }).subscribe();
    httpMock.expectOne(`${base}/categories`).flush({
      ...MOCK_CATEGORIES[0], id: 3, name: 'NewCat', slug: 'newcat',
    });
    expect(service.categories().length).toBe(2);
  });

  // ── error handling ────────────────────────────────────────────────────────

  it('getAll() should propagate errors', (done) => {
    service.getAll().subscribe({
      error: (err) => {
        expect(err.status).toBe(500);
        done();
      },
    });
    const req = httpMock.expectOne(`${base}/categories`);
    req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
  });
});
