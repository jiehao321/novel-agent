'use client';
import { useState, useEffect } from 'react';
import { Card, Tabs, Table, Spin, message, Tag, Descriptions, Button, Modal, Input, Space, Dropdown } from 'antd';
import { useRouter } from 'next/navigation';
const { TextArea } = Input;

const API_BASE = 'http://localhost:8000';

export default function NovelDetail({ params }: { params: { id: string } }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const [writingChapter, setWritingChapter] = useState<number | null>(null);
  const [reviewModal, setReviewModal] = useState<{visible: boolean, chapterNum: number, content: string}>({visible: false, chapterNum: 0, content: ''});
  const [rollbackModal, setRollbackModal] = useState<{visible: boolean, chapterNum: number, versions: any[]}>({visible: false, chapterNum: 0, versions: []});
  const [reviewNote, setReviewNote] = useState('');
  const router = useRouter();
  const novelId = parseInt(params.id);

  const fetchNovel = () => {
    fetch(`${API_BASE}/api/novel/${novelId}`).then(r=>r.json()).then(setNovel).catch(()=>message.error('加载失败')).finally(()=>setLoading(false));
  };

  useEffect(() => { fetchNovel(); }, []);

  const writeChapter = async (chapterNum: number) => {
    setWritingChapter(chapterNum);
    try {
      const res = await fetch(`${API_BASE}/api/novel/${novelId}/chapter/${chapterNum}/write`, { method: 'POST' });
      const data = await res.json();
      if (data.error) {
        message.error(`写作失败: ${data.error}`);
      } else {
        message.success(`章节${chapterNum}写作完成 (重试${data.retries || 0}次)`);
        fetchNovel();
      }
    } catch (e: any) {
      message.error(`异常: ${e.message}`);
    } finally {
      setWritingChapter(null);
    }
  };

  const requestReview = async (chapterNum: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/novel/${novelId}/chapter/${chapterNum}/request-review`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        message.success('已提交人工复审请求');
        fetchNovel();
      } else {
        message.error(data.detail || '请求失败');
      }
    } catch (e: any) {
      message.error(`异常: ${e.message}`);
    }
  };

  const showRollbackVersions = async (chapterNum: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/novel/${novelId}/chapter/${chapterNum}/versions`);
      const data = await res.json();
      setRollbackModal({ visible: true, chapterNum, versions: data.versions || [] });
    } catch (e: any) {
      message.error(`获取版本失败: ${e.message}`);
    }
  };

  const doRollback = async (targetVersion?: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/novel/${novelId}/chapter/${rollbackModal.chapterNum}/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chapter_num: rollbackModal.chapterNum, target_version: targetVersion })
      });
      const data = await res.json();
      if (data.success) {
        message.success(`已回滚到版本${data.version_num}`);
        setRollbackModal({ visible: false, chapterNum: 0, versions: [] });
        fetchNovel();
      } else {
        message.error(data.detail || '回滚失败');
      }
    } catch (e: any) {
      message.error(`异常: ${e.message}`);
    }
  };

  const viewChapterContent = async (chapterNum: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/novel/${novelId}/chapter/${chapterNum}`);
      const data = await res.json();
      setReviewModal({ visible: true, chapterNum, content: data.content || '' });
    } catch (e: any) {
      message.error(`获取内容失败: ${e.message}`);
    }
  };

  if (loading) return <div style={{padding:100,textAlign:'center'}}><Spin/></div>;
  const outline = novel?.outline || {}; 
  const chapters = outline.chapters || []; 
  const chars = novel?.characters || [];
  const chapterDetails = novel?.chapter_details || [];

  const getChapterStatus = (num: number) => {
    const detail = chapterDetails.find((c: any) => c.chapter_num === num);
    return detail?.status || 'not_started';
  };

  const getStatusTag = (status: string) => {
    const tagMap: Record<string, {color: string, text: string}> = {
      'not_started': {color: 'default', text: '未开始'},
      'draft': {color: 'blue', text: '草稿'},
      'pending_review': {color: 'orange', text: '待审核'},
      'approved': {color: 'green', text: '已通过'},
      'rejected': {color: 'red', text: '已拒绝'},
      'failed': {color: 'red', text: '失败'},
      'rolled_back': {color: 'purple', text: '已回滚'},
      'needs_revision': {color: 'orange', text: '需修改'},
    };
    const t = tagMap[status] || {color: 'default', text: status};
    return <Tag color={t.color}>{t.text}</Tag>;
  };

  const chapterColumns = [
    { title: '章', dataIndex: 'num', width: 50, key: 'num' },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '状态', key: 'status', render: (_: any, r: any) => getChapterStatus(r.num) },
    { 
      title: '操作', 
      key: 'actions',
      render: (_: any, r: any) => {
        const status = getChapterStatus(r.num);
        return (
          <Space>
            <Button size="small" type="primary" loading={writingChapter === r.num}
              onClick={() => writeChapter(r.num)} disabled={status === 'pending_review'}>
              {status === 'not_started' ? '写作' : '重写'}
            </Button>
            <Button size="small" onClick={() => viewChapterContent(r.num)}>查看</Button>
            <Button size="small" onClick={() => showRollbackVersions(r.num)}>版本/回滚</Button>
            <Button size="small" type="default" onClick={() => requestReview(r.num)}
              disabled={status !== 'draft' && status !== 'approved' && status !== 'needs_revision'}>
              人工复审
            </Button>
          </Space>
        );
      }
    }
  ];

  return (
    <div style={{padding:20,background:'#f5f5f5',minHeight:'100vh'}}>
      <Card>
        <h1>{outline.title||'未命名'}</h1>
        <div><Tag>{novel?.genre}</Tag><Tag>{chapters.length}章</Tag></div>
        <Tabs items={[
          {key:'o',label:'大纲',children:<Card size="small"><Descriptions column={2}><Descriptions.Item label="开头">{outline.main_plot?.beginning}</Descriptions.Item><Descriptions.Item label="高潮">{outline.main_plot?.climax}</Descriptions.Item></Descriptions></Card>},
          {key:'c',label:'角色',children:<div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,200px)',gap:16}}>{chars.map((c:any,i:number)=><Card key={i} size="small"><Tag color={c.role==='主角'?'red':'blue'}>{c.role}</Tag><p>{c.name}</p></Card>)}</div>},
          {key:'ch',label:'章节',children:<Table dataSource={chapters} rowKey="num" size="small" pagination={false} columns={chapterColumns}/>}
        ]}/>
      </Card>

      {/* 查看章节内容弹窗 */}
      <Modal title={`第${reviewModal.chapterNum}章内容`} open={reviewModal.visible} onCancel={()=>setReviewModal({visible:false,chapterNum:0,content:''})} width={800} footer={null}>
        <div style={{maxHeight: 400, overflow: 'auto', whiteSpace: 'pre-wrap'}}>{reviewModal.content}</div>
      </Modal>

      {/* 回滚弹窗 */}
      <Modal title={`第${rollbackModal.chapterNum}章版本历史`} open={rollbackModal.visible} onCancel={()=>setRollbackModal({visible:false,chapterNum:0,versions:[]})} footer={null}>
        {rollbackModal.versions.length === 0 ? <p>暂无版本记录</p> : (
          <Table size="small" dataSource={rollbackModal.versions} rowKey="version_num" pagination={false}
            columns={[
              { title: '版本', dataIndex: 'version_num', key: 'version_num' },
              { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => getStatusTag(s) },
              { title: '字数', dataIndex: 'word_count', key: 'word_count' },
              { title: '创建者', dataIndex: 'created_by', key: 'created_by' },
              { title: '时间', dataIndex: 'created_at', key: 'created_at' },
              { 
                title: '操作', 
                key: 'action',
                render: (_: any, r: any) => (
                  <Button size="small" onClick={() => doRollback(r.version_num)}>回滚到此版本</Button>
                )
              }
            ]}
          />
        )}
        {rollbackModal.versions.length > 1 && (
          <div style={{marginTop: 16}}>
            <Button type="primary" danger onClick={() => doRollback()}>回滚到上一版本</Button>
          </div>
        )}
      </Modal>
    </div>
  );
}
