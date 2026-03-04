'use client';

// 首页 - 小说创作入口 - 优化版
import { useState } from 'react';
import { Card, Input, Button, Select, message, Spin, Result, Steps, Progress, Divider } from 'antd';
import { BookOutlined, RocketOutlined, CheckCircleOutlined, EditOutlined, TeamOutlined, GlobalOutlined } from '@ant-design/icons';
import { novelAPI } from '../lib/api';
import Link from 'next/link';

const { TextArea } = Input;
const { Option } = Select;

const genreOptions = [
  { value: '都市', label: '🏙️ 都市', desc: '现代都市生活' },
  { value: '都市修仙', label: '⚡ 都市修仙', desc: '都市+修仙结合' },
  { value: '玄幻', label: '🐉 玄幻', desc: '东方奇幻世界' },
  { value: '仙侠', label: '🗡️ 仙侠', desc: '修真仙侠世界' },
  { value: '科幻', label: '🚀 科幻', desc: '未来科技世界' },
  { value: '历史', label: '📜 历史', desc: '历史穿越改编' },
  { value: '游戏', label: '🎮 游戏', desc: '游戏异世界' },
  { value: '悬疑', label: '🔍 悬疑', desc: '推理侦探故事' },
];

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0); // 0: 输入, 1: 创建中, 2: 规划中, 3: 完成
  const [novelId, setNovelId] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  
  const [requirement, setRequirement] = useState('');
  const [genre, setGenre] = useState('都市修仙');

  const handleCreate = async () => {
    if (!requirement.trim()) {
      message.error('请输入小说创作需求');
      return;
    }

    if (requirement.length < 10) {
      message.warning('需求描述太短，请详细描述您的想法');
      return;
    }

    setLoading(true);
    setStep(1);
    
    try {
      // 1. 创建小说
      message.loading({ content: '正在创建小说...', key: 'create' });
      const createRes = await novelAPI.createNovel(requirement, genre);
      const id = createRes.data.novel_id;
      setNovelId(id);
      message.success({ content: '小说创建成功!', key: 'create' });
      
      // 2. 生成大纲
      setStep(2);
      message.loading({ content: 'AI正在生成大纲...', key: 'plan' });
      const planRes = await novelAPI.planNovel(id);
      setResult(planRes.data);
      message.success({ content: '大纲生成完成!', key: 'plan' });
      
      setStep(3);
      
    } catch (error: any) {
      console.error(error);
      message.error(error.response?.data?.detail || '创建失败，请重试');
      setStep(0);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep(0);
    setNovelId(null);
    setResult(null);
    setRequirement('');
  };

  // 完成页面
  if (step === 3 && result) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '40px 20px'
      }}>
        <Card style={{ maxWidth: 800, margin: '0 auto', borderRadius: 16 }}>
          <Result
            icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            title="🎉 小说创作成功！"
            subTitle={result.title}
          />
          
          <Divider />
          
          <div style={{ marginBottom: 24 }}>
            <h3>📖 大纲预览</h3>
            <Card size="small" style={{ background: '#f5f5f5' }}>
              <p><strong>类型：</strong>{result.title?.genre || genre}</p>
              <p><strong>章节数：</strong>{result.chapters_count} 章</p>
              <p><strong>主线：</strong>{result.outline?.main_plot?.beginning || '待生成'}</p>
            </Card>
          </div>
          
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
            <Link href={`/novel/${novelId}`}>
              <Button type="primary" size="large" icon={<BookOutlined />}>
                查看小说
              </Button>
            </Link>
            <Button size="large" onClick={handleReset}>
              创作新小说
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // 加载中
  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Card style={{ maxWidth: 500, textAlign: 'center', borderRadius: 16 }}>
          <Spin size="large" />
          <h2 style={{ marginTop: 24 }}>
            {step === 1 ? '🚀 创建小说中...' : '📝 生成大纲中...'}
          </h2>
          <p style={{ color: '#888', marginTop: 8 }}>
            AI正在为您创作，请稍候...
          </p>
          <Progress 
            percent={step === 1 ? 30 : 70} 
            status="active" 
            style={{ marginTop: 24 }}
          />
        </Card>
      </div>
    );
  }

  // 创建表单
  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '40px 20px'
    }}>
      <Card style={{ maxWidth: 700, margin: '0 auto', borderRadius: 16, boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
        {/* 标题 */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ fontSize: 32, marginBottom: 8 }}>
            <BookOutlined /> Novel Agent
          </h1>
          <p style={{ color: '#888', fontSize: 14 }}>
            基于 32 Agent 的智能小说创作系统
          </p>
        </div>
        
        {/* 步骤条 */}
        <Steps 
          current={step} 
          style={{ marginBottom: 32 }}
          items={[
            { title: '输入需求', icon: <EditOutlined /> },
            { title: '创建小说', icon: <BookOutlined /> },
            { title: 'AI创作', icon: <RocketOutlined /> },
            { title: '完成', icon: <CheckCircleOutlined /> },
          ]}
        />
        
        <Divider />
        
        {/* 类型选择 */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', marginBottom: 12, fontWeight: 'bold' }}>
            🏷️ 选择小说类型
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
            {genreOptions.map(opt => (
              <Card 
                key={opt.value}
                size="small"
                hoverable
                onClick={() => setGenre(opt.value)}
                style={{ 
                  borderColor: genre === opt.value ? '#1890ff' : '#d9d9d9',
                  background: genre === opt.value ? '#e6f7ff' : '#fff'
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div>{opt.label}</div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* 需求输入 */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', marginBottom: 8, fontWeight: 'bold' }}>
            ✍️ 描述您的想法
          </label>
          <TextArea 
            rows={6} 
            placeholder={`描述你想要的小说...

例如：写一个100万字的都市修仙小说，主角原本是天才却修为尽失，经过种种磨难最终成为武帝。包含以下元素：
- 修炼体系
- 门派争斗
- 感情纠葛
- 升级路线`}
            value={requirement}
            onChange={(e) => setRequirement(e.target.value)}
            style={{ fontSize: 14 }}
          />
          <div style={{ marginTop: 8, color: '#888', fontSize: 12 }}>
            字数：{requirement.length} 字 (建议50字以上)
          </div>
        </div>

        {/* 提交按钮 */}
        <Button 
          type="primary" 
          size="large" 
          icon={<RocketOutlined />}
          onClick={handleCreate}
          block
          style={{ height: 48, fontSize: 16 }}
        >
          开始创作
        </Button>

        {/* 底部说明 */}
        <div style={{ marginTop: 24, textAlign: 'center', color: '#888', fontSize: 12 }}>
          <p>✦ 32 Agent 协同工作 ✦ 自动规划大纲 ✦ 多维度审核 ✦</p>
        </div>
      </Card>
    </div>
  );
}
