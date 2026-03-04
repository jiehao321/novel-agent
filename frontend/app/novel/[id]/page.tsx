"""
小说详情页 - 大纲展示、章节管理
"""
import { useState, useEffect } from 'react';
import { Card, Tabs, Table, Button, Spin, message, Tag, Menu } from 'antd';
import { BookOutlined, ReadOutlined, CheckCircleOutlined, DashboardOutlined, EditOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { novelAPI } from '../../lib/api';

import { Collapse } from 'antd';
const { Panel } = Collapse;

export default function NovelDetail({ novelId }: { novelId: number }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('outline');

  useEffect(() => {
    loadNovel();
  }, [novelId]);

  const loadNovel = async () => {
    try {
      const res = await novelAPI.getNovel(novelId);
      setNovel(res.data);
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  if (!novel) {
    return <div>小说不存在</div>;
  }

  const chapters = novel.outline?.chapters || [];
  const characters = novel.characters || [];

  const tabItems = [
    {
      key: 'outline',
      label: '📋 大纲',
      children: (
        <Card title="故事大纲">
          <Collapse defaultActiveKey={['main']}>
            <Panel header="主线剧情" key="main">
              <pre>{JSON.stringify(novel.outline?.main_plot, null, 2)}</pre>
            </Panel>
            <Panel header="支线剧情" key="sub">
              <pre>{JSON.stringify(novel.outline?.sub_plots, null, 2)}</pre>
            </Panel>
            <Panel header="伏笔系统" key="foreshadowing">
              <pre>{JSON.stringify(novel.outline?.foreshadowing, null, 2)}</pre>
            </Panel>
          </Collapse>
        </Card>
      )
    },
    {
      key: 'characters',
      label: '👥 角色',
      children: (
        <Card title="角色档案">
          {characters.map((char: any, i: number) => (
            <Card key={i} size="small" style={{ marginBottom: 10 }}>
              <Tag color="blue">{char.role}</Tag>
              <strong>{char.name}</strong>
              <p>{char.psychology?.core_motivation}</p>
            </Card>
          ))}
        </Card>
      )
    },
    {
      key: 'chapters',
      label: '📖 章节',
      children: (
        <Card 
          title="章节列表"
          extra={
            <Link href={`/novel/${novelId}/progress`}>
              <Button type="primary" icon={<DashboardOutlined />}>
                写作进度
              </Button>
            </Link>
          }
        >
          <Table
            dataSource={chapters}
            rowKey="num"
            pagination={false}
            columns={[
              { title: '章节', dataIndex: 'num', width: 80 },
              { title: '标题', dataIndex: 'title' },
              { title: '核心事件', dataIndex: 'core_event' },
              {
                title: '状态',
                dataIndex: 'status',
                render: (status: string) => (
                  <Tag color={status === 'published' ? 'green' : 'default'}>
                    {status === 'published' ? '已完成' : '待写作'}
                  </Tag>
                )
              }
            ]}
          />
        </Card>
      )
    }
  ];

  return (
    <div style={{ padding: 20, maxWidth: 1400, margin: '0 auto' }}>
      <Card 
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <BookOutlined style={{ fontSize: 24 }} />
            <span>{novel.outline?.title || '未命名小说'}</span>
          </div>
        }
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            <Tag color="purple">{novel.genre}</Tag>
            <Link href={`/novel/${novelId}/outline`}>
              <Button icon={<EditOutlined />}>大纲确认</Button>
            </Link>
            <Link href={`/novel/${novelId}/review`}>
              <Button icon={<CheckCircleOutlined />}>审核详情</Button>
            </Link>
            <Link href={`/novel/${novelId}/monitor`}>
              <Button icon={<DashboardOutlined />}>质量监控</Button>
            </Link>
          </div>
        }
      >
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab} 
          items={tabItems}
        />
      </Card>
    </div>
  );
}
