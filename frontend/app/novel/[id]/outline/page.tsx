'use client';
import { useState, useEffect } from 'react';
import { Card, Button, message, Spin, Tree, Collapse, Table, Tag, Empty, Row, Col, Progress, Timeline } from 'antd';
import { CheckOutlined, EditOutlined } from '@ant-design/icons';
import { novelAPI } from '../../../../lib/api';

// 使用动态导入或直接使用SVG图标
const BookIcon = () => <span style={{ marginRight: 8 }}>📖</span>;
const RhythmIcon = () => <span style={{ marginRight: 8 }}>⚡</span>;
const TreeIcon = () => <span style={{ marginRight: 8 }}>📋</span>;
const CharacterIcon = () => <span style={{ marginRight: 8 }}>👥</span>;

const { Panel } = Collapse;

interface Volume {
  id: number;
  volume_num: number;
  title: string;
  introduction: string;
  start_chapter: number;
  end_chapter: number;
  theme: string;
  core_conflict: string;
  plot_summary: string;
  key_events: { chapter: number; event: string; importance: number }[];
  rhythm_curve: { type: string; points: { position: number; intensity: number; phase: string }[] };
  character_appearances: { name: string; status: string; description: string }[];
}

interface RhythmPoint {
  chapter: number;
  position: number;
  intensity: number;
  phase: string;
  volume_num: number;
}

interface OverallRhythm {
  points: RhythmPoint[];
  major_climaxes: { volume_num: number; chapter: number; title: string; intensity: number }[];
  total_volumes: number;
  total_chapters: number;
}

export default function OutlineConfirm({ params }: { params: { id: string } }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const [volumes, setVolumes] = useState<Volume[]>([]);
  const [overallRhythm, setOverallRhythm] = useState<OverallRhythm | null>(null);
  const [expandedVolumes, setExpandedVolumes] = useState<number[]>([]);
  const novelId = parseInt(params.id);

  useEffect(() => {
    loadData();
  }, [novelId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [novelRes, volumesRes, rhythmRes] = await Promise.all([
        novelAPI.getNovel(novelId),
        novelAPI.getVolumes(novelId),
        novelAPI.getOverallRhythm(novelId).catch(() => ({ data: { rhythm: null } }))
      ]);
      
      setNovel(novelRes.data);
      setVolumes(volumesRes.data?.volumes || []);
      setOverallRhythm(rhythmRes.data?.rhythm || null);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 生成卷目录树数据
  const getVolumeTreeData = () => {
    const chapters = novel?.outline?.chapters || [];
    
    return volumes.map((volume: Volume) => ({
      key: `volume-${volume.volume_num}`,
      title: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <span>
            <BookIcon />
            第{volume.volume_num}卷：{volume.title}
          </span>
          <Tag color="blue">第{volume.start_chapter}-{volume.end_chapter}章</Tag>
        </div>
      ),
      children: chapters
        .filter((ch: any) => ch.num >= volume.start_chapter && ch.num <= volume.end_chapter)
        .map((ch: any) => ({
          key: `chapter-${ch.num}`,
          title: (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>第{ch.num}章：{ch.title}</span>
              <Tag color={ch.foreshadowing?.length > 0 ? 'orange' : 'default'}>
                {ch.core_event?.substring(0, 15) || '无'}
              </Tag>
            </div>
          ),
          isLeaf: true
        }))
    }));
  };

  // 渲染节奏曲线图
  const renderRhythmCurve = () => {
    if (!overallRhythm || !overallRhythm.points.length) {
      return <Empty description="暂无节奏数据" />;
    }

    const maxIntensity = Math.max(...overallRhythm.points.map((p: RhythmPoint) => p.intensity));
    
    return (
      <div style={{ padding: '20px 0' }}>
        <Row gutter={16}>
          <Col span={16}>
            <div style={{ position: 'relative', height: '200px', borderLeft: '2px solid #ddd', borderBottom: '2px solid #ddd' }}>
              {overallRhythm.points.map((point: RhythmPoint, index: number) => (
                <div
                  key={index}
                  style={{
                    position: 'absolute',
                    left: `${point.position}%`,
                    bottom: `${(point.intensity / maxIntensity) * 100}%`,
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: point.phase === '高潮' ? '#ff4d4f' : 
                                     point.phase === '发展' ? '#faad14' : 
                                     point.phase === '铺垫' ? '#1890ff' : '#52c41a',
                    transform: 'translateX(-50%)',
                    cursor: 'pointer'
                  }}
                  title={`第${point.chapter}章 - ${point.phase} (强度: ${point.intensity})`}
                />
              ))}
              {/* 连接线 */}
              <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
                <polyline
                  points={overallRhythm.points
                    .map((p: RhythmPoint) => `${p.position}%,${100 - (p.intensity / maxIntensity) * 100}%`)
                    .join(' ')}
                  fill="none"
                  stroke="#1890ff"
                  strokeWidth="2"
                />
              </svg>
              {/* 整体高潮标记 */}
              {overallRhythm.major_climaxes.map((climax: any, idx: number) => {
                const pos = (climax.chapter / overallRhythm.total_chapters) * 100;
                return (
                  <div
                    key={idx}
                    style={{
                      position: 'absolute',
                      left: `${pos}%`,
                      bottom: '0',
                      width: '2px',
                      height: '100%',
                      backgroundColor: '#ff4d4f',
                      opacity: 0.5
                    }}
                  />
                );
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 12, color: '#666' }}>
              <span>第1章</span>
              <span>第{Math.floor(overallRhythm.total_chapters / 2)}章</span>
              <span>第{overallRhythm.total_chapters}章</span>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 16 }}>
              <h4>节奏图例</h4>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <Tag color="blue">铺垫</Tag>
                <Tag color="gold">发展</Tag>
                <Tag color="red">高潮</Tag>
                <Tag color="green">回落</Tag>
              </div>
            </div>
            <div>
              <h4>整体高潮点</h4>
              {overallRhythm.major_climaxes.map((climax: any, idx: number) => (
                <div key={idx} style={{ marginBottom: 8 }}>
                  <Tag color="red">卷{climax.volume_num}</Tag>
                  <span>第{climax.chapter}章: {climax.title}</span>
                </div>
              ))}
            </div>
          </Col>
        </Row>
      </div>
    );
  };

  // 渲染卷详情
  const renderVolumeDetails = () => {
    if (!volumes.length) {
      return <Empty description="暂无卷结构，请先生成大纲" />;
    }

    return (
      <Collapse 
        accordion 
        activeKey={expandedVolumes}
        onChange={(keys) => {
          const keyArray = Array.isArray(keys) ? keys : [keys];
          setExpandedVolumes(keyArray.map(k => Number(k)));
        }}
      >
        {volumes.map((volume: Volume) => (
          <Panel 
            header={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>
                  <BookIcon />
                  第{volume.volume_num}卷：{volume.title}
                </span>
                <Tag color="blue">第{volume.start_chapter}-{volume.end_chapter}章</Tag>
              </div>
            } 
            key={volume.volume_num}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Card size="small" title="📖 卷简介" style={{ marginBottom: 16 }}>
                  {volume.introduction || volume.plot_summary || '暂无简介'}
                </Card>
                <Card size="small" title="🎯 核心信息" style={{ marginBottom: 16 }}>
                  <p><strong>卷主题：</strong>{volume.theme || '暂无'}</p>
                  <p><strong>核心冲突：</strong>{volume.core_conflict || '暂无'}</p>
                </Card>
                <Card size="small" title="⚡ 关键事件">
                  <Timeline>
                    {volume.key_events?.map((event: any, idx: number) => (
                      <Timeline.Item 
                        key={idx} 
                        color={event.importance >= 9 ? 'red' : event.importance >= 7 ? 'blue' : 'gray'}
                      >
                        <p>第{event.chapter}章：{event.event}</p>
                      </Timeline.Item>
                    )) || <Empty description="暂无关键事件" />}
                  </Timeline>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="📈 卷节奏曲线" style={{ marginBottom: 16 }}>
                  {volume.rhythm_curve?.points?.length ? (
                    <div style={{ height: '150px', position: 'relative', borderLeft: '1px solid #ddd', borderBottom: '1px solid #ddd' }}>
                      {volume.rhythm_curve.points.map((point: any, idx: number) => (
                        <div
                          key={idx}
                          style={{
                            position: 'absolute',
                            left: `${point.position}%`,
                            bottom: `${(point.intensity / 10) * 100}%`,
                            width: '6px',
                            height: '6px',
                            borderRadius: '50%',
                            backgroundColor: point.phase === '高潮' ? '#ff4d4f' : '#1890ff',
                            transform: 'translateX(-50%)'
                          }}
                          title={`${point.phase}: ${point.intensity}`}
                        />
                      ))}
                    </div>
                  ) : (
                    <Empty description="暂无节奏数据" />
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginTop: 4 }}>
                    <span>铺垫</span>
                    <span>发展</span>
                    <span>高潮</span>
                    <span>回落</span>
                  </div>
                </Card>
                <Card size="small" title="👥 出场人物">
                  {volume.character_appearances?.length ? (
                    <div style={{ maxHeight: '200px', overflow: 'auto' }}>
                      {volume.character_appearances.map((char: any, idx: number) => (
                        <div key={idx} style={{ marginBottom: 8, padding: 8, background: '#f5f5f5', borderRadius: 4 }}>
                          <strong>{char.name}</strong>
                          <Tag color={char.status === '退场' ? 'red' : char.status === '命运变化' ? 'orange' : 'green'} style={{ marginLeft: 8 }}>
                            {char.status}
                          </Tag>
                          <p style={{ margin: '4px 0 0', fontSize: 12, color: '#666' }}>{char.description}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <Empty description="暂无出场人物" />
                  )}
                </Card>
              </Col>
            </Row>
          </Panel>
        ))}
      </Collapse>
    );
  };

  if (loading) return <div style={{textAlign:'center',padding:100}}><Spin/></div>;

  return (
    <div style={{ padding: 20 }}>
      <h2 style={{ marginBottom: 20 }}>
        <BookIcon />
        大纲详情 - {novel?.title || '未命名'}
      </h2>
      
      <Row gutter={16}>
        <Col span={24}>
          <Card 
            title={
              <span>
                <TreeIcon />
                卷目录结构
              </span>
            } 
            style={{ marginBottom: 16 }}
          >
            {volumes.length > 0 ? (
              <Tree
                showLine
                defaultExpandAll
                treeData={getVolumeTreeData()}
                style={{ background: '#fafafa', padding: 16, borderRadius: 8 }}
              />
            ) : (
              <Empty description="暂无卷结构，请先生成大纲" />
            )}
          </Card>
        </Col>
      </Row>
      
      <Row gutter={16}>
        <Col span={24}>
          <Card 
            title={
              <span>
                <RhythmIcon />
                整体节奏曲线
              </span>
            } 
            style={{ marginBottom: 16 }}
          >
            {renderRhythmCurve()}
          </Card>
        </Col>
      </Row>
      
      <Row gutter={16}>
        <Col span={24}>
          <Card 
            title={
              <span>
                <BookIcon />
                卷详情
              </span>
            } 
          >
            {renderVolumeDetails()}
          </Card>
        </Col>
      </Row>
      
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="📋 原始大纲数据">
            <pre style={{ maxHeight: '400px', overflow: 'auto', fontSize: 12 }}>
              {JSON.stringify(novel?.outline, null, 2)}
            </pre>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
