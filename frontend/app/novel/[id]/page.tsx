'use client';

// 小说详情页 - 优化版
import { useState, useEffect } from 'react';
import { Card, Tabs, Divider, Table, Button, Spin, message, Tag, Menu, Layout, Typography, Descriptions, Progress, Timeline } from 'antd';
import { BookOutlined, ReadOutlined, CheckCircleOutlined, DashboardOutlined, EditOutlined, SettingOutlined, HomeOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { novelAPI } from '../../lib/api';

const { Header, Content, Sider } = Layout;
const { Title, Paragraph } = Typography;

export default function NovelDetail({ novelId }: { novelId: number }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('outline');
  const router = useRouter();

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
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#f5f5f5'
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (!novel) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <Title level={4}>小说不存在</Title>
        <Link href="/"><Button type="primary">返回首页</Button></Link>
      </div>
    );
  }

  const outline = novel.outline || {};
  const chapters = outline.chapters || [];
  const characters = novel.characters || [];
  const mainPlot = outline.main_plot || {};

  // 菜单项
  const menuItems = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: <Link href="/">首页</Link>,
    },
    {
      key: 'outline',
      icon: <EditOutlined />,
      label: <Link href={`/novel/${novelId}/outline`}>大纲确认</Link>,
    },
    {
      key: 'progress',
      icon: <ReadOutlined />,
      label: <Link href={`/novel/${novelId}/progress`}>写作进度</Link>,
    },
    {
      key: 'review',
      icon: <CheckCircleOutlined />,
      label: <Link href={`/novel/${novelId}/review`}>审核详情</Link>,
    },
    {
      key: 'monitor',
      icon: <DashboardOutlined />,
      label: <Link href={`/novel/${novelId}/monitor`}>质量监控</Link>,
    },
  ];

  // 大纲Tab内容
  const OutlineContent = () => (
    <Card title="📖 主线剧情" size="small">
      <Descriptions column={2} size="small">
        <Descriptions.Item label="开头">{mainPlot.beginning || '-'}</Descriptions.Item>
        <Descriptions.Item label="高潮">{mainPlot.climax || '-'}</Descriptions.Item>
        <Descriptions.Item label="发展">{mainPlot.development || '-'}</Descriptions.Item>
        <Descriptions.Item label="结局">{mainPlot.ending || '-'}</Descriptions.Item>
      </Descriptions>
      
      <Divider />
      
      <Title level={5}>📚 章节规划</Title>
      <Timeline>
        {chapters.map((ch: any, idx: number) => (
          <Timeline.Item key={idx} color={idx === 0 ? 'green' : 'blue'}>
            <Tag>第{ch.num}章</Tag> {ch.title} - {ch.core_event}
          </Timeline.Item>
        ))}
      </Timeline>
    </Card>
  );

  // 角色Tab内容
  const CharactersContent = () => (
    <Card title="👥 角色阵容" size="small">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 16 }}>
        {characters.map((char: any, idx: number) => (
          <Card key={idx} size="small" hoverable>
            <Tag color={char.role === '主角' ? 'red' : 'blue'}>{char.role}</Tag>
            <Title level={5} style={{ marginTop: 8 }}>{char.name}</Title>
            <Paragraph ellipsis={{ rows: 2 }} style={{ fontSize: 12, color: '#888' }}>
              {char.psychology?.core_motivation || '暂无描述'}
            </Paragraph>
          </Card>
        ))}
      </div>
    </Card>
  );

  // 章节Tab内容
  const ChaptersContent = () => (
    <Card 
      title="📖 章节列表"
      extra={
        <Link href={`/novel/${novelId}/progress`}>
          <Button type="primary" icon={<ReadOutlined />}>写作进度</Button>
        </Link>
      }
    >
      <Table
        dataSource={chapters}
        rowKey="num"
        pagination={{ pageSize: 10 }}
        columns={[
          { title: '章节', dataIndex: 'num', width: 60, render: (n: number) => <Tag>{n}</Tag> },
          { title: '标题', dataIndex: 'title' },
          { title: '核心事件', dataIndex: 'core_event', ellipsis: true },
          { 
            title: '伏笔', 
            dataIndex: 'foreshadowing',
            render: (fs: any) => fs?.length > 0 ? <Tag color="orange">{fs.length}个</Tag> : '-'
          },
          {
            title: '操作',
            render: (_, record: any) => (
              <Button size="small" type="link">查看</Button>
            )
          }
        ]}
      />
    </Card>
  );

  const tabItems = [
    { key: 'outline', label: '📋 大纲', children: <OutlineContent /> },
    { key: 'characters', label: '👥 角色', children: <CharactersContent /> },
    { key: 'chapters', label: '📖 章节', children: <ChaptersContent /> },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center' }}>
        <Link href="/">
          <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
            <BookOutlined /> Novel Agent
          </Title>
        </Link>
        <span style={{ marginLeft: 'auto', color: '#888' }}>
          当前小说：《{outline.title || '未命名'}》
        </span>
      </Header>
      
      <Layout>
        <Sider width={200} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
          <Menu
            mode="inline"
            defaultSelectedKeys={['outline']}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        
        <Content style={{ padding: '24px', background: '#f5f5f5' }}>
          <Card>
            <div style={{ marginBottom: 16 }}>
              <Title level={3} style={{ margin: 0 }}>
                📚 {outline.title || '未命名小说'}
              </Title>
              <div style={{ marginTop: 8 }}>
                <Tag color="purple">{novel.genre}</Tag>
                <Tag color="blue">{chapters.length} 章</Tag>
                <Tag color="green">{characters.length} 角色</Tag>
              </div>
            </div>
            
            <Tabs 
              activeKey={activeTab} 
              onChange={setActiveTab} 
              items={tabItems}
            />
          </Card>
        </Content>
      </Layout>
    </Layout>
  );
}
