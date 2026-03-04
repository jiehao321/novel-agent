// 前端 API 客户端
import axios from 'axios';

// 根据环境选择 API 地址
// 开发环境使用 localhost，生产环境使用后端服务地址
const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // 浏览器环境
    if (process.env.NEXT_PUBLIC_API_URL) {
      return process.env.NEXT_PUBLIC_API_URL;
    }
    // 尝试使用当前主机（服务器IP）
    return window.location.protocol + '//' + window.location.hostname + ':8000';
  }
  return 'http://localhost:8000';
};

const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 添加请求拦截器用于调试
if (typeof window !== 'undefined') {
  api.interceptors.request.use(
    (config) => {
      console.log('[API Request]', config.method?.toUpperCase(), config.url, config.data);
      return config;
    },
    (error) => {
      console.error('[API Error]', error);
      return Promise.reject(error);
    }
  );

  // 添加响应拦截器
  api.interceptors.response.use(
    (response) => {
      console.log('[API Response]', response.status, response.config.url);
      return response;
    },
    (error) => {
      console.error('[API Error]', error.response?.status, error.message, error.config?.url);
      return Promise.reject(error);
    }
  );
}

export const novelAPI = {
  // 创建小说
  createNovel: (requirement: string, genre: string) =>
    api.post('/api/novel/create', { requirement, genre, use_mock: true }),
  
  // 获取小说信息
  getNovel: (novelId: number) =>
    api.get(`/api/novel/${novelId}`),
  
  // 生成大纲
  planNovel: (novelId: number) =>
    api.post(`/api/novel/${novelId}/plan`),
  
  // 写章节
  writeChapter: (novelId: number, chapterNum: number) =>
    api.post(`/api/novel/${novelId}/chapter/${chapterNum}/write`),
  
  // 审核章节
  reviewChapter: (novelId: number, chapterNum: number) =>
    api.post(`/api/novel/${novelId}/chapter/${chapterNum}/review`),
  
  // 获取章节
  getChapter: (novelId: number, chapterNum: number) =>
    api.get(`/api/novel/${novelId}/chapter/${chapterNum}`),
  
  // 写所有章节
  writeAllChapters: (novelId: number) =>
    api.post(`/api/novel/${novelId}/write-all`),
};

export default api;
