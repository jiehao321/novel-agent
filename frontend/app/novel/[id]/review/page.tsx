'use client';
import { useState, useEffect } from 'react';
import { Card, Table, Tag, message, Spin } from 'antd';
import { novelAPI } from '../../../../lib/api';

export default function ReviewDetail({ params }: { params: { id: string } }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const novelId = parseInt(params.id);

  useEffect(() => {
    novelAPI.getNovel(novelId).then(r => setNovel(r.data)).finally(() => setLoading(false));
  }, [novelId]);

  if (loading) return <div style={{textAlign:'center',padding:100}}><Spin/></div>;

  const chapters = novel?.outline?.chapters || [];

  return (
    <div style={{padding:20}}>
      <Card title="🔍 审核详情">
        <Table dataSource={chapters} rowKey="num" pagination={false}
          columns={[
            {title:'章节',dataIndex:'num'},
            {title:'标题',dataIndex:'title'},
            {title:'核心事件',dataIndex:'core_event'},
            {title:'状态',render:()=><Tag>待审核</Tag>}
          ]}
        />
      </Card>
    </div>
  );
}
