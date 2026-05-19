export interface User {
  id: number;
  username: string;
  name: string | null;
  trustLevel: number;
  admin: boolean;
  moderator: boolean;
  active: boolean;
  staged: boolean;
  createdAt: string;
  lastSeenAt: string | null;
  avatarUrl: string;
  email?: string | null;
}

export interface CategoryRecentTopic {
  id: number;
  title: string;
  slug: string | null;
  lastPostedAt: string | null;
  postsCount: number;
  authorUsername: string | null;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  color: string;
  textColor: string;
  description: string | null;
  topicCount: number;
  postCount: number;
  parentCategoryId: number | null;
  readRestricted: boolean;
  position: number | null;
  topicTemplate: string | null;
  emoji: string | null;
  icon: string | null;
  createdAt: string;
  latestTopics: CategoryRecentTopic[];
}

export interface Topic {
  id: number;
  title: string;
  fancyTitle: string | null;
  slug: string | null;
  excerpt: string | null;
  postsCount: number;
  replyCount: number;
  views: number;
  likeCount: number;
  categoryId: number | null;
  userId: number | null;
  visible: boolean;
  closed: boolean;
  archived: boolean;
  pinnedGlobally: boolean;
  pinnedAt: string | null;
  archetype: string;
  createdAt: string;
  updatedAt: string;
  bumpedAt: string;
  lastPostedAt: string | null;
  authorUsername: string | null;
  authorName: string | null;
  authorAvatarUrl: string | null;
}

export interface TopicDetail extends Topic {
  canEdit: boolean;
  canClose: boolean;
}

export interface Post {
  id: number;
  userId: number | null;
  topicId: number;
  postNumber: number;
  raw: string;
  cooked: string;
  replyToPostNumber: number | null;
  replyCount: number;
  likeCount: number;
  reads: number;
  postType: number;
  version: number;
  wiki: boolean;
  hidden: boolean;
  userDeleted: boolean;
  createdAt: string;
  updatedAt: string;
  deletedAt: string | null;
  editReason: string | null;
  authorUsername: string | null;
  authorName: string | null;
  authorAvatarUrl: string | null;
  canEdit: boolean;
  canDelete: boolean;
  likedByMe: boolean;
  bookmarkedByMe: boolean;
}

export interface TopicWithPosts {
  topic: TopicDetail;
  posts: Post[];
  totalPosts: number;
  page: number;
  perPage: number;
}

export interface TopicListResponse {
  topics: Topic[];
  total: number;
  page: number;
  perPage: number;
}

export interface CategoryListResponse {
  categories: Category[];
}

export interface SearchResult {
  topicId: number;
  title: string;
  slug: string | null;
  excerpt: string;
  categoryId: number | null;
  createdAt: string;
  postsCount: number;
  authorUsername: string | null;
  rank: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}
