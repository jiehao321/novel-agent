'use client';

// 大纲确认页面
import { useState, useEffect } from 'react';
import { Card, Button, List, Tag, Modal, Input, message, Spin, Result } from 'antd';
import { CheckOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons';
import { novelAPI } from '../../lib/api';

const { TextArea } = Input;

export default function OutlineConfirm({ novelId }: { novelId: number }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editContent, setEditContent] = useState('');

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

  const handleConfirm = async () => {
    try {
      message.success('大纲已确认，开始写作！');
      // 跳转到写作页面或开始写作
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleEdit = () => {
    if (novel?.outline) {
      setEditContent(JSON.stringify(novel.outline, null, 2));
      setEditModalVisible(true);
    }
  };

  const handleSaveEdit = async () => {
    try {
      message.success('大纲已更新');
      setEditModalVisible(false);
      loadNovel();
    } catch (error) {
      message.error('保存失败');
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  if (!novel) {
    return <Result status="error" title="加载失败" />;
  }

  const outline = novel.outline || {};
  const characters = novel.characters || [];

  return (
    <div style={{ padding: 20, maxWidth: 1200, margin: '0 auto' }}>
      <Card
        title="📋 大纲确认"
        extra={
          <div>
            <Button icon={<EditOutlined />} onClick={handleEdit} style={{ marginRight: 8 }}>
              编辑大纲
            </Button>
            <Button type="primary" icon={<CheckOutlined />} onClick={handleConfirm}>
              确认大纲
            </Button>
          </div>
        }
      >
        {/* 基本信息 */}
        <Card type="inner" title="基本信息" style={{ marginBottom: 16 }}>
          <p><strong>标题：</strong>{outline.title}</p>
          <p><strong>类型：</strong>{outline.genre}</p>
          <p><strong>主题：</strong>{outline.theme}</p>
        </Card>

        {/* 主线剧情 */}
        <Card type="inner" title="主线剧情" style={{ marginBottom: 16 }}>
          {outline.main_plot && (
            <div>
              <p><strong>开头：</strong>{outline.main_plot.beginning}</p>
              <p><strong>发展：</strong>{outline.main_plot.development}</p>
              <p><strong>高潮：</strong>{outline.main_plot.climax}</p>
              <p><strong>结局：</strong>{outline.main_plot.ending}</p>
            </div>
          )}
        </Card>

        {/* 支线剧情 */}
        <Card type="inner" title="支线剧情" style={{ marginBottom: 16 }}>
          {outline.sub_plots?.map((plot: any, index: number) => (
            <Tag key={index} style={{ marginBottom: 8 }}>{plot.name}: {plot.description}</Tag>
          ))}
        </Card>

        {/* 章节规划 */}
        <Card type="inner" title="章节规划" style={{ marginBottom: 16 }}>
          <List
            size="small"
            dataSource={outline.chapters || []}
            renderItem={(item: any) => (
              <List.Item>
                <Tag color="blue">第{item.num}章</Tag>
                {item.title} - {item.core_event}
              </List.Item>
            )}
          />
        </Card>

        {/* 角色 */}
        <Card type="inner" title="角色">
          <List
            size="small"
            dataSource={characters}
            renderItem={(item: any) => (
              <List.Item>
                <Tag color={item.role === '主角' ? 'red' : 'green'}>{item.role}</Tag>
                {item.name}
              </List.Item>
            )}
          />
        </Card>
      </Card>

      {/* 编辑弹窗 */}
      <Modal
        title="编辑大纲"
        open={editModalVisible}
        onOk={handleSaveEdit}
        onCancel={() => setEditModalVisible(false)}
        width={800}
      >
        <TextArea 
          rows={20} 
          value={editContent} 
          onChange={(e) => setEditContent(e.target.value)} 
        />
      </Modal>
    </div>
  );
}
