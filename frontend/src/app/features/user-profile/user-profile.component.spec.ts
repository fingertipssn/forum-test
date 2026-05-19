import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ActivatedRoute } from '@angular/router';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { UserProfileComponent } from './user-profile.component';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/auth/auth.service';
import { environment } from '../../../environments/environment';

const base = environment.apiUrl;

const MOCK_USER = {
  id: 1,
  username: 'alice',
  name: 'Alice Smith',
  trustLevel: 2,
  admin: false,
  moderator: false,
  active: true,
  staged: false,
  createdAt: '2024-01-01T00:00:00',
  lastSeenAt: '2024-06-01T00:00:00',
  avatarUrl: 'https://example.com/alice.jpg',
  email: 'alice@example.com',
};

describe('UserProfileComponent', () => {
  let component: UserProfileComponent;
  let fixture: ComponentFixture<UserProfileComponent>;
  let httpMock: HttpTestingController;

  const currentUserSignal = signal<any>(null);
  const mockAuthService = {
    currentUser: currentUserSignal,
    isAuthenticated: signal(false),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        UserProfileComponent,
        HttpClientTestingModule,
        RouterTestingModule,
      ],
      providers: [
        ApiService,
        { provide: AuthService, useValue: mockAuthService },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: () => 'alice' } },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UserProfileComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);
    expect(component).toBeTruthy();
  });

  it('should load user on init', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);
    fixture.detectChanges();

    expect(component.user()?.username).toBe('alice');
    expect(component.loading()).toBeFalse();
  });

  it('should stop loading on error', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(
      'Not found',
      { status: 404, statusText: 'Not Found' }
    );
    fixture.detectChanges();

    expect(component.loading()).toBeFalse();
    expect(component.user()).toBeNull();
  });

  // ── isOwnProfile ──────────────────────────────────────────────────────────

  it('isOwnProfile should be false when not logged in', () => {
    currentUserSignal.set(null);
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);
    fixture.detectChanges();

    expect(component.isOwnProfile()).toBeFalse();
  });

  it('isOwnProfile should be true when viewing own profile', () => {
    currentUserSignal.set({ ...MOCK_USER, id: 1 });
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);
    fixture.detectChanges();

    expect(component.isOwnProfile()).toBeTrue();
  });

  it('isOwnProfile should be false for another user', () => {
    currentUserSignal.set({ id: 99, username: 'bob' });
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);
    fixture.detectChanges();

    expect(component.isOwnProfile()).toBeFalse();
  });

  // ── startEditName / cancelEditName ────────────────────────────────────────

  it('startEditName should populate editNameValue and set editingName=true', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);
    fixture.detectChanges();

    component.startEditName();
    expect(component.editingName()).toBeTrue();
    expect(component.editNameValue()).toBe('Alice Smith');
  });

  it('cancelEditName should set editingName=false', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);

    component.startEditName();
    component.cancelEditName();
    expect(component.editingName()).toBeFalse();
  });

  // ── saveName ──────────────────────────────────────────────────────────────

  it('saveName should PUT to /u/:username and update user signal', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);
    fixture.detectChanges();

    component.startEditName();
    component.editNameValue.set('Alice Updated');
    component.saveName();

    const req = httpMock.expectOne(`${base}/u/alice`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ name: 'Alice Updated' });
    req.flush({ ...MOCK_USER, name: 'Alice Updated' });

    expect(component.user()?.name).toBe('Alice Updated');
    expect(component.editingName()).toBeFalse();
    expect(component.savingName()).toBeFalse();
  });

  it('saveName should set savingName=false on error', () => {
    spyOn(window, 'alert');
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);
    fixture.detectChanges();

    component.startEditName();
    component.saveName();

    const req = httpMock.expectOne(`${base}/u/alice`);
    req.flush('Error', { status: 500, statusText: 'Internal Server Error' });

    expect(component.savingName()).toBeFalse();
  });

  it('saveName should do nothing when user is null', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/u/alice`).flush(MOCK_USER);

    component.user.set(null);
    component.saveName();
    httpMock.expectNone(`${base}/u/alice`);
  });
});
