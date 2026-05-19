import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { BookmarksComponent } from './bookmarks.component';
import { ApiService } from '../../core/services/api.service';
import { environment } from '../../../environments/environment';

const base = environment.apiUrl;

const MOCK_BOOKMARKS = [
  {
    postId: 1,
    postNumber: 3,
    topicId: 10,
    topicTitle: 'Angular 17 Tips',
    topicSlug: 'angular-17-tips',
    categoryId: 1,
    excerpt: 'Learn about signals and standalone components.',
    bookmarkedAt: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
    authorUsername: 'alice',
    authorName: 'Alice Smith',
    authorAvatarUrl: 'https://example.com/alice.jpg',
  },
];

describe('BookmarksComponent', () => {
  let component: BookmarksComponent;
  let fixture: ComponentFixture<BookmarksComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        BookmarksComponent,
        HttpClientTestingModule,
        RouterTestingModule,
      ],
      providers: [ApiService],
    }).compileComponents();

    fixture = TestBed.createComponent(BookmarksComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/bookmarks`).flush({ bookmarks: [] });
    expect(component).toBeTruthy();
  });

  it('should show spinner while loading', () => {
    fixture.detectChanges();
    expect(component.loading()).toBeTrue();
    httpMock.expectOne(`${base}/bookmarks`).flush({ bookmarks: [] });
  });

  it('should display empty state when no bookmarks', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/bookmarks`).flush({ bookmarks: [] });
    fixture.detectChanges();

    expect(component.loading()).toBeFalse();
    expect(component.bookmarks().length).toBe(0);
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-state')).toBeTruthy();
  });

  it('should display bookmark cards when bookmarks exist', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/bookmarks`).flush({ bookmarks: MOCK_BOOKMARKS });
    fixture.detectChanges();

    expect(component.bookmarks().length).toBe(1);
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.bookmark-card')).toBeTruthy();
    expect(compiled.textContent).toContain('Angular 17 Tips');
  });

  it('should show error message on API failure', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/bookmarks`).flush(
      'Error',
      { status: 500, statusText: 'Internal Server Error' }
    );
    fixture.detectChanges();

    expect(component.error()).toBeTruthy();
    expect(component.loading()).toBeFalse();
  });

  // ── displayName helper ────────────────────────────────────────────────────

  it('displayName() should return authorName if set', () => {
    const bk: any = { authorName: 'Alice Smith', authorUsername: 'alice' };
    expect(component.displayName(bk)).toBe('Alice Smith');
  });

  it('displayName() should fall back to authorUsername', () => {
    const bk: any = { authorName: null, authorUsername: 'alice' };
    expect(component.displayName(bk)).toBe('alice');
  });

  it('displayName() should return ? when both are null', () => {
    const bk: any = { authorName: null, authorUsername: null };
    expect(component.displayName(bk)).toBe('?');
  });

  // ── hasRealAvatar ─────────────────────────────────────────────────────────

  it('hasRealAvatar() should return false for null URL', () => {
    const bk: any = { authorAvatarUrl: null };
    expect(component.hasRealAvatar(bk)).toBeFalse();
  });

  it('hasRealAvatar() should return false for letter_avatar URL', () => {
    const bk: any = { authorAvatarUrl: 'https://example.com/letter_avatar_proxy/40/a/1.png' };
    expect(component.hasRealAvatar(bk)).toBeFalse();
  });

  it('hasRealAvatar() should return true for real photo URL', () => {
    const bk: any = { authorAvatarUrl: 'https://cdn.example.com/uploads/user.jpg' };
    expect(component.hasRealAvatar(bk)).toBeTrue();
  });

  // ── letterFor ─────────────────────────────────────────────────────────────

  it('letterFor() should return first letter of username uppercased', () => {
    const bk: any = { authorUsername: 'alice' };
    expect(component.letterFor(bk)).toBe('A');
  });

  it('letterFor() should return ? when username is null', () => {
    const bk: any = { authorUsername: null };
    expect(component.letterFor(bk)).toBe('?');
  });
});
