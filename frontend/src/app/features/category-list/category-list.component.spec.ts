import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { signal } from '@angular/core';
import { CategoryListComponent } from './category-list.component';
import { ApiService } from '../../core/services/api.service';
import { CategoryService } from '../../core/services/category.service';
import { AuthService } from '../../core/auth/auth.service';
import { ComposerStateService } from '../composer/composer-state.service';
import { environment } from '../../../environments/environment';

const base = environment.apiUrl;

const MOCK_CATEGORIES = [
  {
    id: 1, name: 'Tech', slug: 'tech', color: '0088CC', textColor: 'FFFFFF',
    description: 'Technology topics', topicCount: 12, postCount: 80,
    parentCategoryId: null, readRestricted: false,
    position: 1, topicTemplate: null, emoji: null, icon: null,
    createdAt: '2024-01-01T00:00:00', latestTopics: [],
  },
  {
    id: 2, name: 'Science', slug: 'science', color: 'FF5733', textColor: 'FFFFFF',
    description: null, topicCount: 5, postCount: 20,
    parentCategoryId: null, readRestricted: false,
    position: 2, topicTemplate: null, emoji: null, icon: null,
    createdAt: '2024-01-01T00:00:00', latestTopics: [],
  },
];

describe('CategoryListComponent', () => {
  let component: CategoryListComponent;
  let fixture: ComponentFixture<CategoryListComponent>;
  let httpMock: HttpTestingController;

  const mockAuthService = {
    currentUser: signal(null),
    isAuthenticated: signal(false),
    isStaff: signal(false),
  };

  const mockComposerService = {
    openNewTopic: jasmine.createSpy('openNewTopic'),
    isOpen: signal(false),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        CategoryListComponent,
        HttpClientTestingModule,
        RouterTestingModule,
      ],
      providers: [
        ApiService,
        CategoryService,
        { provide: AuthService, useValue: mockAuthService },
        { provide: ComposerStateService, useValue: mockComposerService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CategoryListComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/categories`).flush({ categories: [] });
    expect(component).toBeTruthy();
  });

  it('should start in loading state', () => {
    fixture.detectChanges();
    expect(component.loading()).toBeTrue();
    httpMock.expectOne(`${base}/categories`).flush({ categories: [] });
  });

  it('should load categories on init', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/categories`).flush({ categories: MOCK_CATEGORIES });
    fixture.detectChanges();

    expect(component.loading()).toBeFalse();
    expect(component.categories().length).toBe(2);
  });

  it('should render category rows', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/categories`).flush({ categories: MOCK_CATEGORIES });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Tech');
    expect(compiled.textContent).toContain('Science');
  });

  it('should show error on API failure', () => {
    fixture.detectChanges();
    httpMock.expectOne(`${base}/categories`).flush(
      'Error',
      { status: 500, statusText: 'Internal Server Error' }
    );
    fixture.detectChanges();

    expect(component.error()).toBeTruthy();
    expect(component.loading()).toBeFalse();
  });

  it('trackById should return the category id', () => {
    const cat: any = { id: 42, name: 'Test' };
    expect(component.trackById(0, cat)).toBe(42);
  });

  it('openNewTopic should call composer service', () => {
    component.openNewTopic(1);
    expect(mockComposerService.openNewTopic).toHaveBeenCalledWith(1);
  });
});
