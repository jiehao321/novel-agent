'use client';
import { useState, useEffect } from 'react';
import { Card, Table, Button, Tag, Modal, Input, Space, message, Spin, Tabs } from 'antd';
const { TextArea } = Input;

const API_BASE = 'http://localhost:8000';

export default function ReviewsPage() {
  const [loading, setLoading] = useState(true);
  const [pendingReviews, setPendingReviews] = useState<any[]>([]);
  const [historyReviews, setHistoryReviews] = useState<any[]>([]);
  const [reviewModal, setReviewModal] = useState<{visible: boolean, review: any | null}>({visible: false, review: null});
  const [reviewAction, setReviewAction] = useState<string>('');
  const [reviewNote, setReviewNote] = useState('');

  const fetchReviews = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/reviews/pending`);
      const data = await res.json();
      setPendingReviews(data.reviews || []);
    } catch (e: any) {
      message.error(`获取待审核列表失败: ${e.message}`);
    }
  };

  const fetchHistory = async () => {
    // 获取所有复审历史（这里简化处理）
    try {
      // 暂时显示空列表
      setHistoryReviews([]);
    } catch (e: any) {
      message.error(`获取历史失败: ${e.message}`);
    }
  };

  useEffect(() => {
    fetchReviews();
    fetchHistory();
    setLoading(false);
    
    // 轮询待审核列表
    const interval = setInterval(fetchReviews, 30000);
    return () => clearInterval(interval);
  }, []);

  const openReviewModal = (review: any) => {
    setReviewModal({ visible: true, review });
    setReviewAction('');
    setReviewNote('');
  };

  const submitReview = async () => {
    if (!reviewAction) {
      message.warning('请选择审核动作');
      return;
    }
    if (!reviewModal.review) return;

    try {
      const res = await fetch(`${API_BASE}/api/reviews/${reviewModal.review.id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          review_id: reviewModal.review.id,
          action: reviewAction,
          reviewer_note: reviewNote
        })
      });
      const data = await res.json();
      if (data.success) {
        message.success(`审核完成: ${reviewAction === 'approve' ? '通过' : reviewAction === 'reject' ? '拒绝' : '需修改'}`);
        setReviewModal({ visible: false, review: null });
        fetchReviews();
      } else {
        message.error(data.detail || '审核失败');
      }
    } catch (e: any) {
      message.error(`异常: ${e.message}`);
    }
  };

  const pendingColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '小说ID', dataIndex: 'novel_id', key: 'novel_id', width: 80 },
    { title: '章节', dataIndex: 'chapter_num', key: 'chapter_num', width: 80 },
    { title: '版本', dataIndex: 'version_num', key: 'version_num', width: 80 },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color="orange">{s}</Tag> },
    { title: '申请时间', dataIndex: 'created_at', key: 'created_at' },
    { 
      title: '操作', 
      key: 'action',
      render: (_: any, r: any) => (
        <Button type="primary" onClick={() => openReviewModal(r)}>审核</Button>
      )
    }
  ];

  const historyColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '小说ID', dataIndex: 'novel_id', key: 'novel_id', width: 80 },
    { title: '章节', dataIndex: 'chapter_num', key: 'chapter_num', width: 80 },
    { title: '版本', dataIndex: 'version_num', key: 'version_num', width: 80 },
    { title: '审核动作', dataIndex: 'reviewer_action', key: 'reviewer_action', 
      render: (a: string) => {
        const color = a === 'approve' ? 'green' : a === 'reject' ? 'red' : 'orange';
        const text = a === 'approve' ? '通过' : a === 'reject' ? '拒绝' : '需修改';
        return <Tag color={color}>{text}</Tag>;
      }
    },
    { title: '备注', dataIndex: 'reviewer_note', key: 'reviewer_note', ellipsis: true },
    { title: '完成时间', dataIndex: 'completed_at', key: 'completed_at' },
  ];

  if (loading) return <div style={{padding:100,textAlign:'center'}}><Spin/></div>;

  return (
    <div style={{padding:20,background:'#f5f5f5',minHeight:'100vh'}}>
      <h1>人工复审管理</h1>
      
      <Card>
        <Tabs items={[
          {
            key: 'pending',
            label: <span>待审核 <Tag color="red">{pendingReviews.length}</Tag></span>,
            children: (
              pendingReviews.length === 0 ? 
                <div style={{padding: 40, textAlign: 'center', color: '#999'}}>暂无待审核的章节</div> :
                <Table dataSource={pendingReviews} rowKey="id" columns={pendingColumns} pagination={false} />
            )
          },
          {
            key: 'history',
            label: '审核历史',
            children: (
              <Table dataSource={historyReviews} rowKey="id" columns={historyColumns} pagination={false} />
            )
          }
        ]} />
      </Card>

      {/* 审核弹窗 */}
      <Modal 
        title={`审核章节 - 第${reviewModal.review?.chapter_num}章`} 
        open={reviewModal.visible} 
        onCancel={() => setReviewModal({ visible: false, review: null })}
        onOk={submitReview}
        okText="提交审核"
        width={800}
      >
        <div style={{marginBottom: 16}}>
          <p><strong>小说ID:</strong> {reviewModal.review?.novel_id}</p>
          <p><strong>章节:</strong> 第{reviewModal.review?.chapter_num}章</p>
          <p><strong>版本:</strong> {reviewModal.review?.version_num}</p>
        </div>
        
        <div style={{marginBottom: 16}}>
          <h4>章节内容预览:</h4>
          <div style={{maxHeight: 300, overflow: 'auto', padding: 12, background: '#f5f5f5', borderRadius: 4, whiteSpace: 'pre-wrap'}}>
            {reviewModal.review?.content?.substring(0, 2000) || '无内容'}
            {reviewModal.review?.content?.length > 2000 && '...'}
          </div>
        </div>

        <div style={{marginBottom: 16}}>
          <h4>审核动作:</h4>
          <Space>
            <Button type={reviewAction === 'approve' ? 'primary' : 'default'} onClick={() => setReviewAction('approve')}>
              通过
            </Button>
            <Button type={reviewAction === 'reject' ? 'primary' : 'default'} danger onClick={() => setReviewAction('reject')}>
              拒绝
            </Button>
            <Button type={reviewAction === 'request_changes' ? 'primary' : 'default'} onClick={() => setReviewAction('request_changes')}>
              需修改
            </Button>
          </Space>
        </div>

        <div>
          <h4>审核备注:</h4>
          <TextArea rows={3} value={reviewNote} onChange={e => setReviewNote(e.target.value)} placeholder="请输入审核备注..." />
        </div>
      </Modal>
    </div>
  );
}
