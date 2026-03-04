'use client';

// 质量监控看板
import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Tag, message, Spin } from 'antd';
import { 
  BookOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined,
  StarOutlined,
  AlertOutlined
} from '@ant-design/icons';
import { novelAPI } from '../../lib/api';

export default function QualityMonitor({ novelId }: { novelId: number }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const [stats, setStats] = useState({
    totalChapters: 0,
    completedChapters: 0,
    avgScore: 0,
    pendingReviews: 0
  });

  useEffect(() => {
    loadData();
  }, [novelId]);

  const loadData = async () => {
    try {
      const res = await novelAPI.getNovel(novelId);
      setNovel(res.data);
      
      const outline = res.data.outline || {};
      const chapters = outline.chapters || [];
      
      // 模拟统计数据（实际应该从后端获取）
      setStats({
        totalChapters: chapters.length,
        completedChapters: chapters.length, // 假设都写完了
        avgScore: 8.2,
        pendingReviews: 0
      });
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  const outline = novel?.outline || {};
  const characters = novel?.characters || [];
  const foreshadowing = outline.foreshadowing || [];

  return (
    <div style={{ padding: 20 }}>
      <h1>📊 质量监控看板</h1>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总章节数"
              value={stats.totalChapters}
              prefix={<BookOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成"
              value={stats.completedChapters}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均质量分"
              value={stats.avgScore}
              prefix={<StarOutlined />}
              suffix="/ 10"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待审核"
              value={stats.pendingReviews}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: stats.pendingReviews > 0 ? '#f5222d' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        {/* 进度 */}
        <Col span={12}>
          <Card title="写作进度">
            <Progress 
              percent={Math.round(stats.completedChapters / (stats.totalChapters || 1) * 100)} 
              status="active"
            />
            <p style={{ textAlign: 'center', color: '#888' }}>
              {stats.completedChapters} / {stats.totalChapters} 章
            </p>
          </Card>
        </Col>

        {/* 质量趋势 */}
        <Col span={12}>
          <Card title="质量趋势">
            <Progress 
              percent={stats.avgScore * 10} 
              status="active"
              strokeColor={{
                '0%': '#f5222d',
                '50%': '#faad14',
                '100%': '#52c41a'
              }}
            />
            <p style={{ textAlign: 'center', color: '#888' }}>
              整体质量评分: {stats.avgScore}/10
            </p>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        {/* 角色统计 */}
        <Col span={12}>
          <Card title="角色统计">
            <p>总角色数: {characters.length}</p>
            <p>主角: {characters.filter((c: any) => c.role === '主角').length}</p>
            <p>配角: {characters.filter((c: any) => c.role === '配角').length}</p>
            <p>反派: {characters.filter((c: any) => c.role === '反派').length}</p>
          </Card>
        </Col>

        {/* 伏笔统计 */}
        <Col span={12}>
          <Card title="伏笔系统">
            <p>总伏笔数: {foreshadowing.length}</p>
            <p>已埋设: {foreshadowing.filter((f: any) => f.status === 'revealed').length}</p>
            <p>待回收: {foreshadowing.filter((f: any) => f.status === 'pending').length}</p>
          </Card>
        </Col>
      </Row>

      {/* 高潮点分布 */}
      <Card title="🎯 高潮点分布" style={{ marginTop: 16 }}>
        {(outline.climax_points || []).map((point: number, index: number) => (
          <Tag key={index} color="red" style={{ marginBottom: 8 }}>
            第{point}章 - 高潮{index + 1}
          </Tag>
        ))}
      </Card>

      {/* 章节质量详情 */}
      <Card title="章节质量详情" style={{ marginTop: 16 }}>
        <Table
          size="small"
          dataSource={(outline.chapters || []).map((ch: any, i: number) => ({
            ...ch,
            quality: 7 + Math.random() * 3, // 模拟数据
            key: i
          }))}
          columns={[
            { title: '章节', dataIndex: 'num', width: 60 },
            { title: '标题', dataIndex: 'title' },
            { 
              title: '质量分',
              dataIndex: 'quality',
              render: (q: number) => (
                <Progress 
                  percent={q * 10} 
                  size="small"
                  strokeColor={q >= 8 ? '#52c41a' : q >= 6 ? '#faad14' : '#f5222d'}
                />
              )
            }
          ]}
          pagination={false}
        />
      </Card>
    </div>
  );
}
