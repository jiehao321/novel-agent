'use client';

// 审核详情页面
import { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Modal, Progress, message, Spin, Result, Tabs } from 'antd';
import { EyeOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { novelAPI } from '../../lib/api';

export default function ReviewDetail({ novelId }: { novelId: number }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const [chapters, setChapters] = useState<any[]>([]);
  const [selectedChapter, setSelectedChapter] = useState<any>(null);
  const [reviewModalVisible, setReviewModalVisible] = useState(false);

  useEffect(() => {
    loadData();
  }, [novelId]);

  const loadData = async () => {
    try {
      const res = await novelAPI.getNovel(novelId);
      setNovel(res.data);
      
      // 加载每个章节的审核结果
      const outline = res.data.outline || {};
      const chapterList = outline.chapters || [];
      
      const chapterData = [];
      for (let ch of chapterList) {
        try {
          const reviewRes = await novelAPI.reviewChapter(novelId, ch.num);
          chapterData.push({
            ...ch,
            review: reviewRes.data,
            status: reviewRes.data?.approved ? 'published' : 'draft'
          });
        } catch {
          chapterData.push({
            ...ch,
            status: 'pending'
          });
        }
      }
      setChapters(chapterData);
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleViewReview = async (chapter: any) => {
    setSelectedChapter(chapter);
    setReviewModalVisible(true);
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return '#52c41a';
    if (score >= 6) return '#faad14';
    return '#f5222d';
  };

  const columns = [
    { title: '章节', dataIndex: 'num', width: 60 },
    { title: '标题', dataIndex: 'title' },
    { title: '核心事件', dataIndex: 'core_event' },
    { 
      title: '审核状态',
      dataIndex: 'status',
      render: (status: string) => (
        <Tag color={status === 'published' ? 'green' : status === 'draft' ? 'orange' : 'default'}>
          {status === 'published' ? '已通过' : status === 'draft' ? '待审核' : '未写作'}
        </Tag>
      )
    },
    {
      title: '质量评分',
      key: 'score',
      render: (_: any, record: any) => {
        if (record.review?.final_score) {
          return (
            <Progress 
              percent={record.review.final_score * 10} 
              size="small"
              strokeColor={getScoreColor(record.review.final_score)}
            />
          );
        }
        return '-';
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Button 
          size="small" 
          icon={<EyeOutlined />}
          onClick={() => handleViewReview(record)}
        >
          查看详情
        </Button>
      )
    }
  ];

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  // 审核维度数据
  const reviewDetails = selectedChapter?.review || {};

  return (
    <div style={{ padding: 20, maxWidth: 1400, margin: '0 auto' }}>
      <Card title="🔍 审核详情">
        <Tabs 
          items={[
            {
              key: 'chapters',
              label: '章节审核',
              children: (
                <Table 
                  columns={columns} 
                  dataSource={chapters} 
                  rowKey="num"
                  pagination={false}
                />
              )
            },
            {
              key: 'summary',
              label: '质量汇总',
              children: (
                <div>
                  <Card type="inner" title="整体质量">
                    <Progress 
                      percent={
                        chapters.filter(c => c.review?.approved).length / (chapters.length || 1) * 100
                      } 
                      status="active"
                    />
                    <p>已通过章节：{chapters.filter(c => c.review?.approved).length} / {chapters.length}</p>
                  </Card>
                  
                  <Card type="inner" title="各维度平均分" style={{ marginTop: 16 }}>
                    {['logic', 'sensitivity', 'originality', 'ai_style', 'consistency', 'foreshadowing'].map(key => {
                      const scores = chapters
                        .filter(c => c.review?.instant?.details?.[key]?.score)
                        .map(c => c.review.instant.details[key].score);
                      const avg = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : '-';
                      return (
                        <p key={key}>
                          <Tag>{key}</Tag> 平均分: {avg}
                        </p>
                      );
                    })}
                  </Card>
                </div>
              )
            }
          ]}
        />
      </Card>

      {/* 审核详情弹窗 */}
      <Modal
        title={`第${selectedChapter?.num}章 审核详情`}
        open={reviewModalVisible}
        onCancel={() => setReviewModalVisible(false)}
        footer={null}
        width={700}
      >
        {selectedChapter && (
          <div>
            <h3>综合评分</h3>
            <Progress 
              percent={reviewDetails.final_score ? reviewDetails.final_score * 10 : 0}
              status={reviewDetails.approved ? 'success' : 'exception'}
            />
            
            <h4>即时审核</h4>
            <Table
              size="small"
              dataSource={Object.entries(reviewDetails.instant?.scores || {}).map(([key, value]: [string, any]) => ({
                dimension: key,
                score: value
              }))}
              columns={[
                { title: '维度', dataIndex: 'dimension' },
                { 
                  title: '评分', 
                  dataIndex: 'score',
                  render: (score: number) => <Progress percent={score * 10} size="small" />
                }
              ]}
              pagination={false}
              rowKey="dimension"
            />
            
            <h4>深度审核</h4>
            <p>文笔质量分: {reviewDetails.deep?.score || '-'}</p>
            
            <h4>审核决策</h4>
            <Tag 
              color={reviewDetails.approved ? 'green' : 'red'}
              icon={reviewDetails.approved ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
            >
              {reviewDetails.approved ? '通过' : '需修改'}
            </Tag>
          </div>
        )}
      </Modal>
    </div>
  );
}
