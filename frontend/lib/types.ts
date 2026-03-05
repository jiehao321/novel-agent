/**
 * Novel Agent API TypeScript 类型定义
 * 统一前后端类型，确保数据一致性
 */

// ========== 基础类型 ==========

/** API版本 */
export const API_VERSION = '1.0.0';

/** 基础响应 */
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: ApiError;
  timestamp: string;
  version: string;
}

/** 错误响应 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

/** 分页参数 */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

// ========== 小说相关类型 ==========

/** 小说类型 */
export type Genre = '玄幻' | '都市' | '历史' | '科幻' | '武侠' | '仙侠' | '游戏' | '其他';

/** 小说状态 */
export type NovelStatus = 'created' | 'planning' | 'planned' | 'writing' | 'completed';

/** 小说 */
export interface Novel {
  id: number;
  title: string;
  genre: Genre;
  requirement: string;
  status: NovelStatus;
  outline?: Outline;
  chapters?: number[];
  chapterDetails?: ChapterStatus[];
  createdAt?: string;
  updatedAt?: string;
}

/** 小说创建请求 */
export interface CreateNovelRequest {
  title?: string;
  requirement: string;
  genre: Genre;
  useMock?: boolean;
}

/** 小说创建响应 */
export interface CreateNovelResponse {
  novelId: number;
  status: string;
  message: string;
}

// ========== 大纲相关类型 ==========

/** 大纲 */
export interface Outline {
  title: string;
  genre: string;
  theme: string;
  totalChapters: number;
  totalVolumes: number;
  mainPlot: PlotSummary;
  subPlots: SubPlot[];
  chapters: ChapterBrief[];
  climaxPoints: number[];
  foreshadowing: Foreshadowing[];
  volumes?: Volume[];
  overallRhythm?: RhythmCurve;
}

/** 剧情概要 */
export interface PlotSummary {
  beginning: string;
  development: string;
  climax: string;
  ending: string;
}

/** 支线剧情 */
export interface SubPlot {
  name: string;
  description: string;
}

// ========== 卷相关类型 ==========

/** 卷 */
export interface Volume {
  volumeNum: number;
  title: string;
  introduction: string;
  startChapter: number;
  endChapter: number;
  theme: string;
  coreConflict: string;
  coreGoal: string;
  plotDirection: string;
  chapterGroups: ChapterGroup[];
  rhythmCurve: RhythmCurve;
  characterAppearances: CharacterAppearance[];
}

/** 章节组 */
export interface ChapterGroup {
  title: string;
  chapters: ChapterBrief[];
}

/** 章节简要信息 */
export interface ChapterBrief {
  num?: number;
  chapterNum?: number;
  title: string;
  coreEvent?: string;
  volume?: number;
  summary?: string;
  conflict?: string;
  爽点?: string;
  hook?: string;
  emotionCurve?: string;
  foreshadowing?: Foreshadowing[];
}

// ========== 章节相关类型 ==========

/** 章节状态 */
export interface ChapterStatus {
  chapterNum: number;
  status: 'draft' | 'reviewing' | 'approved' | 'rejected';
  error?: string;
  retryCount?: number;
}

/** 章节内容 */
export interface Chapter {
  novelId: number;
  chapterNum: number;
  versionNum: number;
  content: string;
  wordCount: number;
  status: string;
  reviewScore?: number;
}

/** 章节创建请求 */
export interface WriteChapterRequest {
  previousChapterSummary?: string;
  genre?: string;
}

// ========== 审核相关类型 ==========

/** 审核结果 */
export interface ReviewResult {
  approved: boolean;
  finalScore: number;
  instant: InstantReview;
  deep?: DeepReview;
  decision: 'approve' | 'revise' | 'reject';
}

/** 即时审核 */
export interface InstantReview {
  approved: boolean;
  scores: ReviewScores;
  avgScore: number;
  details: ReviewDetails;
}

/** 审核分数 */
export interface ReviewScores {
  logic: number;
  sensitivity: number;
  originality: number;
  aiStyle: number;
  consistency: number;
  foreshadowing: number;
}

/** 审核详情 */
export interface ReviewDetails {
  logic?: unknown;
  sensitivity: ReviewCheckResult;
  originality: ReviewCheckResult;
  aiStyle: ReviewCheckResult;
  consistency?: unknown;
  foreshadowing?: ReviewCheckResult;
}

/** 审核检查结果 */
export interface ReviewCheckResult {
  approved: boolean;
  score: number;
  issues: string[];
  suggestions: string[];
}

/** 深度审核 */
export interface DeepReview {
  approved: boolean;
  score: number;
  improvements: string[];
}

// ========== 节奏曲线类型 ==========

/** 节奏曲线 */
export interface RhythmCurve {
  type: 'standard' | 'custom';
  preparation: number;
  development: number;
  climax: number;
  falling: number;
  points: RhythmPoint[];
}

/** 节奏点 */
export interface RhythmPoint {
  chapter?: number;
  position: number;
  intensity: number;
  phase: string;
  volumeNum?: number;
}

// ========== 人物相关类型 ==========

/** 人物 */
export interface Character {
  name: string;
  role: string;
  psychology?: CharacterPsychology;
  behavior?: CharacterBehavior;
  relationships?: CharacterRelationship[];
}

/** 人物心理 */
export interface CharacterPsychology {
  coreMotivation?: string;
  [key: string]: unknown;
}

/** 人物行为 */
export interface CharacterBehavior {
  decisionPattern?: string;
  [key: string]: unknown;
}

/** 人物关系 */
export interface CharacterRelationship {
  name: string;
  role: string;
  relationship: string;
}

/** 人物出场 */
export interface CharacterAppearance {
  name: string;
  status: string;
  description: string;
}

// ========== 伏笔相关类型 ==========

/** 伏笔 */
export interface Foreshadowing {
  id?: string;
  description: string;
  plantChapter: number;
  revealChapter: number;
}

// ========== 复审相关类型 ==========

/** 复审请求 */
export interface ManualReviewRequest {
  reviewId?: number;
  chapterNum: number;
  action: 'approve' | 'reject' | 'revise';
  reviewerNote?: string;
}

/** 复审状态 */
export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'revision_requested';

// ========== WebSocket相关类型 ==========

/** WebSocket消息类型 */
export type WebSocketMessageType = 
  | 'stage_start'
  | 'stage_progress'
  | 'stage_complete'
  | 'stage_error'
  | 'chapter_progress'
  | 'chapter_complete'
  | 'overall_progress';

/** WebSocket消息 */
export interface WebSocketMessage {
  type: WebSocketMessageType;
  stage?: string;
  progress: number;
  message: string;
  data?: Record<string, unknown>;
}

/** 进度数据 */
export interface ProgressData {
  overallProgress: number;
  currentStage: string;
  stageProgress: number;
  stages: StageInfo[];
  chapterProgress?: ChapterProgressInfo[];
}

/** 阶段信息 */
export interface StageInfo {
  name: string;
  progress: number;
  status: 'pending' | 'running' | 'completed' | 'error';
}

/** 章节进度信息 */
export interface ChapterProgressInfo {
  chapterNum: number;
  progress: number;
  status: 'pending' | 'writing' | 'completed' | 'error';
}

// ========== 错误码 ==========

export const ErrorCode = {
  // 通用错误
  BAD_REQUEST: 'BAD_REQUEST',
  NOT_FOUND: 'NOT_FOUND',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  
  // 业务错误
  NOVEL_NOT_FOUND: 'NOVEL_NOT_FOUND',
  CHAPTER_NOT_FOUND: 'CHAPTER_NOT_FOUND',
  NOVEL_NOT_PLANNED: 'NOVEL_NOT_PLANNED',
  NOVEL_ALREADY_PLANNED: 'NOVEL_ALREADY_PLANNED',
  REVIEW_NOT_FOUND: 'REVIEW_NOT_FOUND',
  VOLUME_NOT_FOUND: 'VOLUME_NOT_FOUND',
} as const;

export type ErrorCodeType = typeof ErrorCode[keyof typeof ErrorCode];
