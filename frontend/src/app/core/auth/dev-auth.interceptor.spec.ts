import { TestBed } from '@angular/core/testing';
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing';
import {
  HTTP_INTERCEPTORS,
  HttpClient,
} from '@angular/common/http';
import { DevAuthInterceptor, DEV_TOKEN_KEY } from './dev-auth.interceptor';

describe('DevAuthInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        {
          provide: HTTP_INTERCEPTORS,
          useClass: DevAuthInterceptor,
          multi: true,
        },
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should pass through requests when no token in localStorage', () => {
    http.get('/api/test').subscribe();
    const req = httpMock.expectOne('/api/test');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('should add Authorization header when token exists', () => {
    const fakeToken = 'my.jwt.token';
    localStorage.setItem(DEV_TOKEN_KEY, fakeToken);

    http.get('/api/test').subscribe();
    const req = httpMock.expectOne('/api/test');
    expect(req.request.headers.get('Authorization')).toBe(`Bearer ${fakeToken}`);
    req.flush({});
  });

  it('should use the exported DEV_TOKEN_KEY constant', () => {
    expect(DEV_TOKEN_KEY).toBe('discourse_dev_token');
  });

  it('should not mutate the original request', () => {
    const fakeToken = 'test-token';
    localStorage.setItem(DEV_TOKEN_KEY, fakeToken);

    http.get('/api/me').subscribe();
    const req = httpMock.expectOne('/api/me');
    // Verify the cloned request has the header, not the original
    expect(req.request.headers.get('Authorization')).toBe(`Bearer ${fakeToken}`);
    req.flush({});
  });

  it('should forward POST requests with token', () => {
    localStorage.setItem(DEV_TOKEN_KEY, 'token123');
    http.post('/api/posts', { raw: 'Hello' }).subscribe();
    const req = httpMock.expectOne('/api/posts');
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('Authorization')).toBe('Bearer token123');
    req.flush({});
  });
});
