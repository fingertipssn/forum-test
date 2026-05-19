import { TestBed } from '@angular/core/testing';
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { AuthService } from './auth.service';
import { DEV_TOKEN_KEY } from './dev-auth.interceptor';
import { environment } from '../../../environments/environment';

const base = environment.apiUrl;

const MOCK_USER = {
  id: 1,
  username: 'alice',
  name: 'Alice Smith',
  trustLevel: 1,
  admin: false,
  moderator: false,
  active: true,
  staged: false,
  createdAt: '2024-01-01T00:00:00',
  lastSeenAt: '2024-06-01T00:00:00',
  avatarUrl: 'https://example.com/alice.jpg',
  email: null,
};

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule],
      providers: [AuthService],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should start with currentUser = null', () => {
    expect(service.currentUser()).toBeNull();
  });

  it('isAuthenticated should be false initially', () => {
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('isStaff should be false initially', () => {
    expect(service.isStaff()).toBeFalse();
  });

  // ── loadCurrentUser ───────────────────────────────────────────────────────

  it('loadCurrentUser() should set currentUser on success', async () => {
    const promise = service.loadCurrentUser();
    const req = httpMock.expectOne(`${base}/auth/me`);
    expect(req.request.method).toBe('GET');
    req.flush(MOCK_USER);
    await promise;

    expect(service.currentUser()).not.toBeNull();
    expect(service.currentUser()?.username).toBe('alice');
    expect(service.isAuthenticated()).toBeTrue();
  });

  it('loadCurrentUser() should clear currentUser on HTTP error', async () => {
    const promise = service.loadCurrentUser();
    const req = httpMock.expectOne(`${base}/auth/me`);
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });
    await promise;

    expect(service.currentUser()).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('isStaff should be true for admin user', async () => {
    const promise = service.loadCurrentUser();
    httpMock.expectOne(`${base}/auth/me`).flush({ ...MOCK_USER, admin: true });
    await promise;
    expect(service.isStaff()).toBeTrue();
  });

  it('isStaff should be true for moderator user', async () => {
    const promise = service.loadCurrentUser();
    httpMock.expectOne(`${base}/auth/me`).flush({ ...MOCK_USER, moderator: true });
    await promise;
    expect(service.isStaff()).toBeTrue();
  });

  // ── logout ────────────────────────────────────────────────────────────────

  it('logout() should clear currentUser', async () => {
    // First log in
    const loadPromise = service.loadCurrentUser();
    httpMock.expectOne(`${base}/auth/me`).flush(MOCK_USER);
    await loadPromise;
    expect(service.currentUser()).not.toBeNull();

    // Now log out (devMode)
    await service.logout();
    expect(service.currentUser()).toBeNull();
  });

  it('logout() should clear currentUser regardless of devMode', async () => {
    // Set a user then log out
    service.currentUser.set({ id: 1, username: 'alice' } as any);
    await service.logout();
    expect(service.currentUser()).toBeNull();
  });

  // ── devLogin ──────────────────────────────────────────────────────────────

  it('devLogin() should store token and set currentUser', async () => {
    const promise = service.devLogin('alice', 'alice@test.com', 'Alice');
    const req = httpMock.expectOne(`${base}/auth/dev-login`);
    expect(req.request.method).toBe('POST');
    req.flush({ access_token: 'test-jwt', user: MOCK_USER });
    await promise;

    expect(localStorage.getItem(DEV_TOKEN_KEY)).toBe('test-jwt');
    expect(service.currentUser()?.username).toBe('alice');
  });
});
