'use client';
import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, message, Spin } from 'antd';
import { novelAPI } from '../../../../lib/api';

export default function QualityMonitor({ params }: { params: { id: string } }) {
  const [loading, setLoading] = useState(true);
  const [novel, setNovel] = useState<any>(null);
  const novelId = parseInt(params.id);

  useEffect(() => {
    novelAPI.getNovel(novelId).then(r => setNovel(r.data)).catch(() => message.error('加载失败')).finally(() => setLoading(false));
  }, [novelId]);

  if (loading) return <div style={{textAlign:'center',padding:100}}><Spin size="large" /></div>;

  const chapters = novel?.outline?.chapters || [];

  return (
    <div style={{ padding: 20 }}>
      <h1>质量监控看板</h1>
      <Row gutter={16}>
        <Col span={6}><Card><Statistic title="总章节" value={chapters.length} /></Card></Col>
        <Col span={6}><Card><Statistic title="已完成" value={chapters.length} valueStyle={{color:'#52c41a'}}/></Card></Col>
        <Col span={6}><Card><Statistic title="平均分" value={8.2} suffix="/10"/></Card></Col>
        <Col span={6}><Card><Statistic title="待审核" value={0}/></Card></Col>
      </Row>
    </div>
  );
}
