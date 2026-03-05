// 增强的 WebSocket 客户端 - 支持断线重连和阶段进度
import { useState, useEffect, useRef, useCallback } from 'react';

// WebSocket 消息类型
const MessageType = {
  STAGE_PROGRESS: 'stage_progress',
  STAGE_START: 'stage_start',
  STAGE_COMPLETE: 'stage_complete',
  STAGE_ERROR: 'stage_error',
  PROGRESS: 'progress',
  CHAPTER_PROGRESS: 'chapter_progress',
  CHAPTER_COMPLETE: 'chapter_complete',
  HEARTBEAT: 'heartbeat',
  PING: 'ping',
  PONG: 'pong',
  CONNECTED: 'connected',
  ERROR: 'error',
  COMPLETED: 'completed'
};

// Agent 阶段
const AgentStage = {
  IDLE: 'idle',
  PLANNING: 'planning',
  GENERATING_OUTLINE: 'generating_outline',
  GENERATING_CHARACTERS: 'generating_characters',
  GENERATING_WORLD: 'generating_world',
  GENERATING_FORESHADOWING: 'generating_foreshadowing',
  WRITING_CHAPTERS: 'writing_chapters',
  REVIEWING: 'reviewing',
  COMPLETED: 'completed'
};

// 阶段中文名称
const StageNames = {
  [AgentStage.IDLE]: '空闲',
  [AgentStage.PLANNING]: '需求分析',
  [AgentStage.GENERATING_OUTLINE]: '生成大纲',
  [AgentStage.GENERATING_CHARACTERS]: '生成角色',
  [AgentStage.GENERATING_WORLD]: '世界观设定',
  [AgentStage.GENERATING_FORESHADOWING]: '伏笔设计',
  [AgentStage.WRITING_CHAPTERS]: '章节写作',
  [AgentStage.REVIEWING]: '审核优化',
  [AgentStage.COMPLETED]: '完成'
};

const getStageName = (stage) => StageNames[stage] || stage;

// 获取 WebSocket URL
const getWsUrl = (novelId) => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = process.env.NEXT_PUBLIC_WS_PORT || '8000';
    return `${protocol}//${host}:${port}/ws/${novelId}`;
  }
  return `ws://localhost:8000/ws/${novelId}`;
};

// 默认配置
const defaultConfig = {
  reconnectInterval: 3000,      // 重连间隔 (ms)
  maxReconnectAttempts: 10,    // 最大重连次数
  heartbeatInterval: 30000,   // 心跳间隔 (ms)
  reconnect: true             // 是否自动重连
};

export function useWebSocket(novelId, config = {}) {
  const options = { ...defaultConfig, ...config };
  
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // disconnected, connecting, connected, error
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  
  // 进度状态
  const [overallProgress, setOverallProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(AgentStage.IDLE);
  const [stageProgress, setStageProgress] = useState(0);
  const [stages, setStages] = useState([]);
  const [chapterProgress, setChapterProgress] = useState({ current: 0, total: 0, progress: 0 });
  
  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const heartbeatTimerRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  // 清理函数
  const cleanup = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // 发送消息
  const sendMessage = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  // 处理消息
  const handleMessage = useCallback((event) => {
    try {
      const message = JSON.parse(event.data);
      setLastMessage(message);
      setError(null);

      switch (message.type) {
        case MessageType.CONNECTED:
          setConnectionStatus('connected');
          reconnectAttemptsRef.current = 0;
          console.log('[WS] Connected:', message);
          break;

        case MessageType.STAGE_PROGRESS:
          setCurrentStage(message.stage);
          setStageProgress(message.progress);
          console.log('[WS] Stage Progress:', message);
          break;

        case MessageType.STAGE_START:
          setCurrentStage(message.stage);
          setStageProgress(0);
          console.log('[WS] Stage Start:', message);
          break;

        case MessageType.STAGE_COMPLETE:
          setCurrentStage(message.stage);
          setStageProgress(100);
          console.log('[WS] Stage Complete:', message);
          break;

        case MessageType.PROGRESS:
          setOverallProgress(message.overall_progress);
          setCurrentStage(message.current_stage);
          setStageProgress(message.stage_progress);
          if (message.stages) {
            setStages(message.stages);
          }
          break;

        case MessageType.CHAPTER_PROGRESS:
          setChapterProgress({
            current: message.chapter_num,
            total: message.total_chapters,
            progress: message.progress
          });
          break;

        case MessageType.CHAPTER_COMPLETE:
          setChapterProgress(prev => ({
            ...prev,
            current: message.chapter_num
          }));
          console.log('[WS] Chapter Complete:', message);
          break;

        case MessageType.COMPLETED:
          setCurrentStage(AgentStage.COMPLETED);
          setOverallProgress(100);
          setStageProgress(100);
          console.log('[WS] Completed:', message);
          break;

        case MessageType.ERROR:
          setError(message.message || message.error);
          console.error('[WS] Error:', message);
          break;

        case MessageType.HEARTBEAT:
        case MessageType.PONG:
          // 心跳响应
          break;

        default:
          console.log('[WS] Unknown message:', message);
      }
    } catch (err) {
      console.error('[WS] Parse error:', err);
    }
  }, []);

  // 重连
  const reconnect = useCallback(() => {
    if (!options.reconnect || reconnectAttemptsRef.current >= options.maxReconnectAttempts) {
      setConnectionStatus('error');
      return;
    }

    reconnectAttemptsRef.current++;
    setConnectionStatus('connecting');
    
    console.log(`[WS] Reconnecting... attempt ${reconnectAttemptsRef.current}`);
    
    reconnectTimerRef.current = setTimeout(() => {
      connect();
    }, options.reconnectInterval);
  }, [options.reconnect, options.reconnectInterval, options.maxReconnectAttempts]);

  // 连接
  const connect = useCallback(() => {
    cleanup();

    const wsUrl = getWsUrl(novelId);
    console.log('[WS] Connecting to:', wsUrl);
    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Open');
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // 启动心跳
        heartbeatTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: MessageType.PING }));
          }
        }, options.heartbeatInterval);
      };

      ws.onmessage = handleMessage;

      ws.onerror = (err) => {
        console.error('[WS] Error:', err);
        setError('WebSocket error');
      };

      ws.onclose = () => {
        console.log('[WS] Close');
        setConnectionStatus('disconnected');
        cleanup();
        reconnect();
      };
    } catch (err) {
      console.error('[WS] Connect error:', err);
      setConnectionStatus('error');
      reconnect();
    }
  }, [novelId, options.heartbeatInterval, cleanup, handleMessage, reconnect]);

  // 初始化连接
  useEffect(() => {
    if (novelId) {
      connect();
    }
    
    return cleanup;
  }, [novelId, connect, cleanup]);

  // 手动重连
  const manualReconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  // 断开连接
  const disconnect = useCallback(() => {
    options.reconnect = false; // 禁用自动重连
    cleanup();
    setConnectionStatus('disconnected');
  }, [cleanup, options]);

  return {
    // 连接状态
    connectionStatus,
    isConnected: connectionStatus === 'connected',
    
    // 错误
    error,
    lastMessage,
    
    // 进度数据
    overallProgress,
    currentStage,
    currentStageName: getStageName(currentStage),
    stageProgress,
    stages,
    chapterProgress,
    
    // 操作
    sendMessage,
    reconnect: manualReconnect,
    disconnect
  };
}

// 进度组件使用的 Hook - 简化版
export function useProgress(novelId) {
  const {
    connectionStatus,
    isConnected,
    overallProgress,
    currentStage,
    currentStageName,
    stageProgress,
    stages,
    chapterProgress,
    error,
    reconnect,
    disconnect
  } = useWebSocket(novelId);

  return {
    // 连接
    connectionStatus,
    isConnected,
    error,
    reconnect,
    disconnect,
    
    // 进度
    overallProgress,
    currentStage,
    currentStageName,
    stageProgress,
    stages,
    
    // 章节
    chapterProgress,
    
    // 状态文本
    statusText: isConnected 
      ? `${currentStageName}: ${stageProgress}%` 
      : connectionStatus === 'connecting' 
        ? '连接中...' 
        : '未连接'
  };
}

export default useWebSocket;
