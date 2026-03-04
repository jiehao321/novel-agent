'use client';

// 实时进度页面
import { useState, useEffect, useRef } from 'react';
import { Card, Progress, Button, List, Tag, Spin, message, Result } from 'antd';
import { SyncOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

export default function WritingProgress({ novelId }: { novelId: number }) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [progress, setProgress] = useState({ current: 0, total: 0, chapter: '', status: '' });
  const [chapters, setChapters] = useState<any[]>([]);
  const [connected, setConnected] = useState(false);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    // 连接 WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/${novelId}`;
    
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      message.success('实时连接已建立');
    };
    
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress') {
          setProgress(data.data);
        } else if (data.type === 'chapter_complete') {
          setChapters(prev => [...prev, data.data]);
        } else if (data.type === 'completed') {
          setCompleted(true);
          message.success('所有章节写作完成！');
        } else if (data.type === 'error') {
          message.error(data.message);
        }
      } catch (e) {
        console.error('Failed to parse message', e);
      }
    };
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error', error);
      message.error('连接失败');
    };
    
    setWs(websocket);
    
    return () => {
      websocket.close();
    };
  }, [novelId]);

  const startWriting = async () => {
    try {
      const response = await fetch(`/api/novel/${novelId}/write-all`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.status === 'completed') {
        message.success('写作任务已启动');
      }
    } catch (error) {
      message.error('启动失败');
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: 800, margin: '0 auto' }}>
      <Card
        title="写作进度"
        extra={
          <Tag color={connected ? 'green' : 'red'}>
            {connected ? '已连接' : '未连接'}
          </Tag>
        }
      >
        {/* 进度条 */}
        <div style={{ marginBottom: 30 }}>
          <Progress 
            percent={progress.total > 0 ? Math.round(progress.current / progress.total * 100) : 0} 
            status={completed ? 'success' : 'active'}
            format={() => `${progress.current}/${progress.total} 章`}
          />
          <p style={{ textAlign: 'center', color: '#888' }}>
            {progress.chapter || '等待开始...'}
          </p>
        </div>
        
        {/* 操作按钮 */}
        {!completed && (
          <div style={{ textAlign: 'center', marginBottom: 30 }}>
            <Button 
              type="primary" 
              icon={<SyncOutlined />}
              onClick={startWriting}
              loading={progress.status === 'writing'}
            >
              开始写作
            </Button>
          </div>
        )}
        
        {/* 章节列表 */}
        <List
          header="已完成的章节"
          dataSource={chapters}
          renderItem={(item: any) => (
            <List.Item>
              <List.Item.Meta
                title={`第${item.chapter_num}章`}
                description={`${item.word_count}字`}
              />
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
            </List.Item>
          )}
          locale={{ emptyText: '暂无完成的章节' }}
        />
        
        {/* 完成提示 */}
        {completed && (
          <Result
            status="success"
            title="写作完成！"
            subTitle={`共完成 ${chapters.length} 章`
            }
          />
        )}
      </Card>
    </div>
  );
}
