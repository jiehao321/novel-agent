'use client';
import { useState, useEffect } from 'react';
import { Card, Progress, Row, Col, Tag, Button, Spin, Alert, Timeline, Space, Statistic } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import { novelAPI } from '../../../../lib/api';
import { useProgress } from '../../../../lib/useWebSocket';

// 状态图标组件
const WifiIcon = ({ status }: { status: string }) => {
  const style = status === 'connected' ? { color: '#52c41a' } : status === 'connecting' ? {} : { color: '#ff4d4f' };
  return <span style={style}>{status === 'connected' ? '🟢' : status === 'connecting' ? '🟡' : '🔴'}</span>;
};

// 完成图标
const CheckIcon = ({ style }: { style?: React.CSSProperties }) => <span style={style}>✅</span>;

// 失败图标
const FailIcon = ({ style }: { style?: React.CSSProperties }) => <span style={style}>❌</span>;

export default function RealTimeProgress({ params }: { params: { id: string } }) {
  const novelId = parseInt(params.id);
  
  // 使用 WebSocket 进度 Hook
  const {
    connectionStatus,
    isConnected,
    error,
    overallProgress,
    currentStage,
    currentStageName,
    stageProgress,
    stages,
    chapterProgress,
    reconnect,
    disconnect
  } = useProgress(novelId);
  
  const [novel, setNovel] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    novelAPI.getNovel(novelId)
      .then(r => setNovel(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [novelId]);

  // 获取连接状态显示
  const getStatusIcon = () => {
    return <WifiIcon status={connectionStatus} />;
  };

  const getStatusText = () => {
    const statusMap = {
      disconnected: '未连接',
      connecting: '连接中...',
      connected: '实时同步',
      error: '连接错误'
    };
    return statusMap[connectionStatus] || connectionStatus;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  const chapters = novel?.outline?.chapters || [];
  const totalChapters = chapters.length;

  return (
    <div style={{ padding: 20, background: '#f5f5f5', minHeight: '100vh' }}>
      <Row gutter={[16, 16]}>
        {/* 顶部状态栏 */}
        <Col span={24}>
          <Card size="small">
            <Row justify="space-between" align="middle">
              <Col>
                <Space>
                  {getStatusIcon()}
                  <span>{getStatusText()}</span>
                  {!isConnected && connectionStatus !== 'connecting' && (
                    <Button size="small" onClick={reconnect}>重连</Button>
                  )}
                </Space>
              </Col>
              <Col>
                <Tag color="blue">{novel?.title || '未命名'}</Tag>
                <Tag>{novel?.genre}</Tag>
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 总体进度 */}
        <Col span={24}>
          <Card title="总体进度">
            <Progress 
              percent={overallProgress} 
              status={overallProgress >= 100 ? 'success' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#52c41a',
              }}
            />
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={6}>
                <Statistic 
                  title="当前阶段" 
                  value={currentStageName} 
                  valueStyle={{ fontSize: 18, color: '#1890ff' }}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="阶段进度" 
                  value={stageProgress} 
                  suffix="%" 
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="章节进度" 
                  value={`${chapterProgress.current || 0}/${chapterProgress.total || totalChapters}`} 
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="总章节" 
                  value={totalChapters} 
                />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 阶段列表 */}
        <Col span={24}>
          <Card title="执行阶段">
            <Timeline
              items={stages.length > 0 ? stages.map((s: any) => ({
                color: s.completed ? 'green' : s.id === currentStage ? 'blue' : 'gray',
                children: (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>{s.name}</span>
                    {s.completed && <CheckIcon />}
                    {s.id === currentStage && (
                      <span style={{ color: '#1890ff' }}>{stageProgress}%</span>
                    )}
                  </div>
                )
              })) : [
                { color: 'gray', children: '等待开始...' }
              ]}
            />
          </Card>
        </Col>

        {/* 章节进度 */}
        <Col span={24}>
          <Card title="章节写作进度">
            {totalChapters > 0 ? (
              <Row gutter={[8, 8]}>
                {chapters.map((ch: any, idx: number) => {
                  const isCurrentChapter = chapterProgress.current === ch.num;
                  const isCompleted = chapterProgress.current > ch.num || (idx === 0 && chapterProgress.current === 0);
                  const isWriting = isCurrentChapter && chapterProgress.progress < 100;
                  
                  return (
                    <Col span={4} key={ch.num}>
                      <Card 
                        size="small"
                        style={{ 
                          background: isCurrentChapter ? '#e6f7ff' : isCompleted ? '#f6ffed' : '#fafafa',
                          borderColor: isCurrentChapter ? '#1890ff' : undefined
                        }}
                      >
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontWeight: 'bold' }}>第{ch.num}章</div>
                          <div style={{ fontSize: 12, color: '#666' }}>{ch.title}</div>
                          {isWriting && (
                            <Progress 
                              percent={chapterProgress.progress} 
                              size="small" 
                              style={{ marginTop: 4 }}
                            />
                          )}
                          {isCompleted && !isWriting && (
                            <CheckIcon style={{ marginTop: 4 }} />
                          )}
                        </div>
                      </Card>
                    </Col>
                  );
                })}
              </Row>
            ) : (
              <Alert message="暂无章节数据，请先生成大纲" type="info" />
            )}
          </Card>
        </Col>

        {/* 错误提示 */}
        {error && (
          <Col span={24}>
            <Alert 
              message="连接错误" 
              description={error} 
              type="error" 
              showIcon 
              action={
                <Button size="small" onClick={reconnect}>重试</Button>
              }
            />
          </Col>
        )}
      </Row>
    </div>
  );
}
