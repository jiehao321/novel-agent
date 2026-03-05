/**
 * Novel Agent API 客户端
 * 统一的API调用层，使用标准化响应格式
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import type { 
  ApiResponse, 
  CreateNovelRequest, 
  CreateNovelResponse,
  Novel,
  Outline,
  Volume,
  RhythmCurve,
  Chapter,
  WriteChapterRequest,
  ReviewResult,
  ManualReviewRequest,
  ApiError
} from './types';


// 根据环境选择 API 地址
const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== 'undefined') {
    return window.location.protocol + '//' + window.location.hostname + ':8000';
  }
  return 'http://localhost:8000';
};

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加调试日志
api.interceptors.request.use(
  (config) => {
    console.log('[API Request]', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('[ Error]', error);
API Request    return Promise.reject(error);
  }
);

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => {
    console.log('[API Response]', response.status, response.config.url);
    },
  ( return response;
 error: AxiosError<ApiResponse<unknown>>) => {
    const status = error.response?.status;
    const data = error.response?.data;
    
    // 提取错误信息
    let errorMessage = error.message;
    let errorCode = 'UNKNOWN_ERROR';
    
    if (data?.error) {
      errorCode = data.error.code;
      errorMessage = data.error.message;
    } else if (data?.message) {
      errorMessage = data.message;
    }
    
    console.error('[API Error]', status, errorCode, errorMessage);
    
    // 返回标准化的错误格式
    return Promise.reject({
      success: false,
      error: {
        code: errorCode,
        message: errorMessage,
        details: error.response?.data
      },
      status
    });
  }
);

// ========== API函数 ==========

export const novelAPI = {
  // ========== 小说相关 ==========
  
  /** 创建小说 */
  createNovel: (data: CreateNovelRequest): Promise<ApiResponse<CreateNovelResponse>> =>
    api.post('/api/novel/create', data),
  
  /** 获取小说信息 */
  getNovel: (novelId: number): Promise<ApiResponse<Novel>> =>
    api.get(`/api/novel/${novelId}`),
  
  /** 生成大纲 */
  planNovel: (novelId: number, data?: { genre?: string; targetChapters?: number }): Promise<ApiResponse<Outline>> =>
    api.post(`/api/novel/${novelId}/plan`, data),
  
  // ========== 章节相关 ==========
  
  /** 写章节 */
  writeChapter: (novelId: number, chapterNum: number, data?: WriteChapterRequest): Promise<ApiResponse<Chapter>> =>
    api.post(`/api/novel/${novelId}/chapter/${chapterNum}/write`, data),
  
  /** 审核章节 */
  reviewChapter: (novelId: number, chapterNum: number): Promise<ApiResponse<ReviewResult>> =>
    api.post(`/api/novel/${novelId}/chapter/${chapterNum}/review`),
  
  /** 获取章节 */
  getChapter: (novelId: number, chapterNum: number): Promise<ApiResponse<Chapter>> =>
    api.get(`/api/novel/${novelId}/chapter/${chapterNum}`),
  
  /** 写所有章节 */
  writeAllChapters: (novelId: number): Promise<ApiResponse<{ chapters: number[] }>> =>
    api.post(`/api/novel/${novelId}/write-all`),
  
  /** 重试写章节 */
  retryWriteChapter: (novelId: number, chapterNum: number): Promise<ApiResponse<Chapter>> =>
    api.post(`/api/novel/${novelId}/chapter/${chapterNum}/retry`),
  
  /** 回滚章节 */
  rollbackChapter: (novelId: number, chapterNum: number, targetVersion?: number): Promise<ApiResponse<Chapter>> =>
    api.post(`/api/novel/${novelId}/chapter/${chapterNum}/rollback`, { 
      chapter_num: chapterNum, 
      target_version: targetVersion 
    }),
  
  /** 获取章节版本历史 */
  getChapterVersions: (novelId: number, chapterNum: number): Promise<ApiResponse<{ versions: unknown[] }>> =>
    api.get(`/api/novel/${novelId}/chapter/${chapterNum}/versions`),
  
  /** 获取指定版本内容 */
  getChapterVersion: (novelId: number, chapterNum: number, versionNum: number): Promise<ApiResponse<Chapter>> =>
    api.get(`/api/novel/${novelId}/chapter/${chapterNum}/version/${versionNum}`),
  
  // ========== 复审相关 ==========
  
  /** 请求人工复审 */
  requestManualReview: (novelId: number, chapterNum: number): Promise<ApiResponse<{ reviewId: number }>> =>
    api.post(`/api/novel/${novelId}/chapter/${chapterNum}/request-review`),
  
  /** 获取待处理的复审请求 */
  getPendingReviews: (): Promise<ApiResponse<unknown[]>> =>
    api.get('/api/reviews/pending'),
  
  /** 获取小说的复审历史 */
  getNovelReviews: (novelId: number): Promise<ApiResponse<unknown[]>> =>
    api.get(`/api/novel/${novelId}/reviews`),
  
  /** 完成人工复审 */
  completeManualReview: (reviewId: number, action: string, reviewerNote: string): Promise<ApiResponse<unknown>> =>
    api.post(`/api/reviews/${reviewId}/complete`, {
      review_id: reviewId,
      action,
      reviewer_note: reviewerNote
    }),
    
  // ========== 卷相关 ==========
  
  /** 获取所有卷 */
  getVolumes: (novelId: number): Promise<ApiResponse<{ volumes: Volume[]; count: number }>> =>
    api.get(`/api/novel/${novelId}/volumes`),
  
  /** 获取指定卷详情 */
  getVolume: (novelId: number, volumeNum: number): Promise<ApiResponse<Volume>> =>
    api.get(`/api/novel/${novelId}/volumes/${volumeNum}`),
  
  /** 获取整体节奏曲线 */
  getOverallRhythm: (novelId: number): Promise<ApiResponse<{ rhythm: RhythmCurve }>> =>
    api.get(`/api/novel/${novelId}/rhythm`),
  
  /** 更新卷信息 */
  updateVolume: (novelId: number, volumeNum: number, data: Partial<Volume>): Promise<ApiResponse<Volume>> =>
    api.post(`/api/novel/${novelId}/volumes/${volumeNum}`, data),
};

export default api;
