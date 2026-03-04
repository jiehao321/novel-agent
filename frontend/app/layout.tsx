import './globals.css';
import 'antd/dist/reset.css';

export const metadata = {
  title: 'Novel Agent - AI 小说创作系统',
  description: '基于多 Agent 的智能小说创作平台',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
