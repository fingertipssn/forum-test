import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ActivatedRoute } from '@angular/router';
import { signal } from '@angular/core';
import { TopicDetailComponent } from './topic-detail.component';
import { ApiService } from '../../core/services/api.service';
import { TopicService } from '../../core/services/topic.service';
import { PostService } from '../../core/services/post.service';
import { AuthService } from '../../core/auth/auth.service';
import { ComposerStateService } from '../composer/composer-state.service';
import { environment } from '../../../environments/environment';

const base = environment.apiUrl;

const MOCK_POST = {
  id: 1,
  userId: 1,
  topicId: 10,
  postNumber: 1,
  raw: 'Hello world',
  cooked: '<p>Hello world</p>',
  replyToPostNumber: null,
  replyCount: 0,
  likeCount: 3,
  reads: 10,
  postType: 1,
  version: 1,
  wiki: false,
  hidden: false,
  userDeleted: false,
  createdAt: '2024-01-01T00:00:00',
  updatedAt: '2024-01-01T00:00:00',
  deletedAt: null,
  editReason: null,
  authorUsername: 'alice',
  authorName: 'Alice Smith',
  authorAvatarUrl: 'https://example.com/alice.jpg',
  canEdit: true,
  canDelete: false,
  likedByMe: false,
  bookmarkedByMe: false,
};

const MOCK_TOPIC_RESPONSE = {
  topic: {
    id: 10,
    title: 'Test Topic',
    fancyTitle: 'Test Topic',
    slug: 'test-topic',
    postsCount: 1,
    replyCount: 0,
    views: 50,
    likeCount: 5,
    categoryId: 1,
    userId: 1,
    visible: true,
    closed: false,
    archived: false,
    pinnedGlobally: false,
    archetype: 'regular',
    createdAt: '2024-01-01T00:00:00',
    updatedAt: '2024-01-01T00:00:00',
    bumpedAt: '2024-01-01T00:00:00',
    lastPostedAt: null,
    authorUsername: 'alice',
    authorAvatarUrl: 'https://example.com/alice.jpg',
    canEdit: true,
    canClose: false,
  },
  posts: [MOCK_POST],
  totalPosts: 1,
  page: 1,
  perPage: 20,
};

describe('TopicDetailComponent', () => {
  let component: TopicDetailComponent;
  let fixture: ComponentFixture<TopicDetailComponent>;
  let httpMock: HttpTestingController;

  const isAuthenticatedSignal = signal(false);
  const currentUserSignal = signal<any>(null);

  const mockAuthService = {
    currentUser: currentUserSignal,
    isAuthenticated: isAuthenticatedSignal,
    isStaff: signal(false),
  };

  const mockComposerService = {
    openReply: jasmine.createSpy('openReply'),
    openNewTopic: jasmine.createSpy('openNewTopic'),
    isOpen: signal(false),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        TopicDetailComponent,
        HttpClientTestingModule,
        RouterTestingModule,
      ],
      providers: [
        ApiService,
        TopicService,
        PostService,
        { provide: AuthService, useValue: mockAuthService },
        { provide: ComposerStateService, useValue: mockComposerService },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: () => '10' } },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(TopicDetailComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  const flushTopic = () => {
    const req = httpMock.expectOne((r) => r.url.includes('/topics/10'));
    req.flush(MOCK_TOPIC_RESPONSE);
  };

  it('should create', () => {
    fixture.detectChanges();
    flushTopic();
    expect(component).toBeTruthy();
  });

  it('should load topic and posts on init', () => {
    fixture.detectChanges();
    flushTopic();
    fixture.detectChanges();

    expect(component.loading()).toBeFalse();
    expect(component.topic()?.title).toBe('Test Topic');
    expect(component.posts().length).toBe(1);
  });

  it('should show error on API failure', () => {
    fixture.detectChanges();
    const req = httpMock.expectOne((r) => r.url.includes('/topics/10'));
    req.flush('Error', { status: 500, statusText: 'Internal Server Error' });
    fixture.detectChanges();

    expect(component.error()).toBeTruthy();
    expect(component.loading()).toBeFalse();
  });

  it('pageNumbers() should return correct array', () => {
    fixture.detectChanges();
    flushTopic();
    fixture.detectChanges();

    component.totalPosts.set(40);
    component.perPage.set(20);
    const pages = component.pageNumbers();
    expect(pages).toEqual([1, 2]);
  });

  it('startEdit() should set editingPostId and editRaw', () => {
    fixture.detectChanges();
    flushTopic();

    component.startEdit(MOCK_POST as any);
    expect(component.editingPostId()).toBe(1);
    expect(component.editRaw()).toBe('Hello world');
  });

  it('cancelEdit() should clear editing state', () => {
    fixture.detectChanges();
    flushTopic();

    component.startEdit(MOCK_POST as any);
    component.cancelEdit();
    expect(component.editingPostId()).toBeNull();
    expect(component.editRaw()).toBe('');
  });

  it('trackById() should return post id', () => {
    expect(component.trackById(0, MOCK_POST as any)).toBe(1);
  });

  // ── toggleLike ────────────────────────────────────────────────────────────

  it('toggleLike() should do nothing when not authenticated', () => {
    isAuthenticatedSignal.set(false);
    fixture.detectChanges();
    flushTopic();

    component.toggleLike(MOCK_POST as any);
    httpMock.expectNone((r) => r.url.includes('/like'));
  });

  it('toggleLike() should update likedByMe and likeCount', () => {
    isAuthenticatedSignal.set(true);
    fixture.detectChanges();
    flushTopic();
    fixture.detectChanges();

    component.toggleLike(MOCK_POST as any);
    const req = httpMock.expectOne(`${base}/posts/1/like`);
    req.flush({ liked: true, likeCount: 4 });

    const updated = component.posts().find(p => p.id === 1);
    expect(updated?.likedByMe).toBeTrue();
    expect(updated?.likeCount).toBe(4);
  });

  // ── toggleBookmark ────────────────────────────────────────────────────────

  it('toggleBookmark() should do nothing when not authenticated', () => {
    isAuthenticatedSignal.set(false);
    fixture.detectChanges();
    flushTopic();

    component.toggleBookmark(MOCK_POST as any);
    httpMock.expectNone((r) => r.url.includes('/bookmark'));
  });

  it('toggleBookmark() should update bookmarkedByMe', () => {
    isAuthenticatedSignal.set(true);
    fixture.detectChanges();
    flushTopic();
    fixture.detectChanges();

    component.toggleBookmark(MOCK_POST as any);
    const req = httpMock.expectOne(`${base}/posts/1/bookmark`);
    req.flush({ bookmarked: true });

    const updated = component.posts().find(p => p.id === 1);
    expect(updated?.bookmarkedByMe).toBeTrue();
  });

  // ── reply ─────────────────────────────────────────────────────────────────

  it('reply() should call composer.openReply with topic info', () => {
    fixture.detectChanges();
    flushTopic();
    fixture.detectChanges();

    component.reply();
    expect(mockComposerService.openReply).toHaveBeenCalledWith(10, 'Test Topic');
  });

  it('replyToPost() should call composer.openReply with post number', () => {
    fixture.detectChanges();
    flushTopic();
    fixture.detectChanges();

    component.replyToPost(MOCK_POST as any);
    expect(mockComposerService.openReply).toHaveBeenCalledWith(10, 'Test Topic', 1);
  });
});
