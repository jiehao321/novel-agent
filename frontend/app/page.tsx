'use client';

// 首页 - 小说创作入口
import { useState } from 'react';
import { Card, Input, Button, Select, message, Spin, Result } from 'antd';
import { BookOutlined, RocketOutlined, LoadingOutlined } from '@ant-design/icons';
import { novelAPI } from '../lib/api';

const { TextArea } = Input;
const { Option } = Select;

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [novelId, setNovelId] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  
  const [requirement, setRequirement] = useState('');
  const [genre, setGenre] = useState('都市');

  const handleCreate = async () => {
    if (!requirement.trim()) {
      message.error('请输入小说需求');
      return;
    }

    setLoading(true);
    try {
      // 1. 创建小说
      const createRes = await novelAPI.createNovel(requirement, genre);
      const id = createRes.data.novel_id;
      setNovelId(id);
      message.success('小说创建成功，正在生成大纲...');

      // 2. 生成大纲
      const planRes = await novelAPI.planNovel(id);
      setResult(planRes.data);
      message.success('大纲生成完成！');
    } catch (error: any) {
      console.error(error);
      message.error(error.response?.data?.detail || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setNovelId(null);
    setResult(null);
    setRequirement('');
  };

  // 加载中
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        flexDirection: 'column'
      }}>
        <Spin size="large" indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} />
        <p style={{ marginTop: 20, fontSize: 18 }}>
          正在创作小说，请稍候...
        </p>
      </div>
    );
  }

  // 结果展示
  if (result) {
    return (
      <div style={{ padding: '40px', maxWidth: 1200, margin: '0 auto' }}>
        <Result
          status="success"
          title="小说创作完成！"
          subTitle={`《${result.title}》`}
          extra={[
            <Button type="primary" key="console" onClick={() => window.location.href = `/novel/${novelId}`}>
              查看大纲
            </Button>,
            <Button key="buy" onClick={handleReset}>
              创作新小说
            </Button>,
          ]}
        />
        
        <Card title="大纲预览" style={{ marginTop: 20 }}>
          <pre style={{ whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto' }}>
            {JSON.stringify(result.outline, null, 2)}
          </pre>
        </Card>
      </div>
    );
  }

  // 创建表单
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card 
        style={{ width: 600, boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}
        title={<><BookOutlined /> Novel Agent - AI 小说创作系统</>}
      >
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>小说类型</label>
          <Select 
            value={genre} 
            onChange={setGenre}
            style={{ width: '100%' }}
          >
            <Option value="都市">都市</Option>
            <Option value="都市修仙">都市修仙</Option>
            <Option value="玄幻">玄幻</Option>
            <Option value="仙侠">仙侠</Option>
            <Option value="科幻">科幻</Option>
            <Option value="历史">历史</Option>
            <Option value="游戏">游戏</Option>
          </Select>
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', marginBottom: 8 }}>创作需求</label>
          <TextArea 
            rows={6} 
            placeholder="描述你想要的小说...
例如：写一个100万字的都市修仙小说，主角从修为尽失到成为武帝"
            value={requirement}
            onChange={(e) => setRequirement(e.target.value)}
          />
        </div>

        <Button 
          type="primary" 
          size="large" 
          icon={<RocketOutlined />}
          onClick={handleCreate}
          block
        >
          开始创作
        </Button>

        <p style={{ marginTop: 20, color: '#888', fontSize: 12, textAlign: 'center' }}>
          基于 32 Agent 多阶段创作系统
        </p>
      </Card>
    </div>
  );
}
