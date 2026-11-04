import type { ReactNode } from 'react';

export type IconName = 'grid'|'chat'|'activity'|'network'|'chart'|'shield'|'arrow'|'check'|'close'|'search'|'chevron'|'refresh'|'database'|'brain'|'book'|'menu'|'flask'|'warning'|'info'|'clock'|'external'|'send'|'leaf'|'spark'|'heart';
const paths: Record<IconName, ReactNode> = {
  grid:<><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
  chat:<><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8A8.5 8.5 0 0 1 12.5 20a8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8A8.5 8.5 0 0 1 8.7 3.9 8.4 8.4 0 0 1 12.5 3h.5a8.5 8.5 0 0 1 8 8v.5Z"/><path d="M8 10h8M8 14h5"/></>,
  activity:<><path d="M3 12h4l3-8 4 16 3-8h4"/></>,
  network:<><circle cx="12" cy="12" r="3"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><path d="m7 7 3 3m4 4 3 3m-3-7 3-3M7 17l3-3"/></>,
  chart:<><path d="M4 3v17h17M8 15v-4m5 4V7m5 8V4"/></>,
  shield:<><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/></>,
  arrow:<><path d="M4 12h16m-6-6 6 6-6 6"/></>,
  check:<path d="m5 12 4 4L19 6"/>, close:<path d="m6 6 12 12M6 18 18 6"/>,
  search:<><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></>,
  chevron:<path d="m9 5 7 7-7 7"/>, refresh:<><path d="M20 7v5h-5M4 17v-5h5"/><path d="M6.1 6A8 8 0 0 1 20 12M4 12a8 8 0 0 0 13.9 6"/></>,
  database:<><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/></>,
  brain:<><path d="M12 4c-4-3-8 1-6 4-4 2-3 7 0 8-1 4 4 7 6 3m0-15c4-3 8 1 6 4 4 2 3 7 0 8 1 4-4 7-6 3V4Z"/><path d="M6 8h2m8 0h2M6 16h2m8 0h2"/></>,
  book:<><path d="M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1v15Z"/></>,
  menu:<path d="M4 6h16M4 12h16M4 18h16"/>,
  flask:<><path d="M9 3h6M10 3v6L4 19a1.4 1.4 0 0 0 1.3 2h13.4a1.4 1.4 0 0 0 1.3-2L14 9V3M7 15h10"/></>,
  warning:<><path d="m12 3 10 17H2L12 3Z"/><path d="M12 9v4m0 3h.01"/></>,
  info:<><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/></>,
  clock:<><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  external:<><path d="M14 3h7v7m0-7L10 14M9 3H4a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-5"/></>,
  send:<><path d="m22 2-7 20-4-9-9-4L22 2ZM22 2 11 13"/></>,
  leaf:<><path d="M20 3c-8-1-16 3-16 10a7 7 0 0 0 7 7c7 0 10-8 9-17Z"/><path d="M3 21 15 9"/></>,
  spark:<><path d="m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5L12 2Z"/></>,
  heart:<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0l-1 1-1-1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>,
};
export function Icon({name,className=''}:{name:IconName;className?:string}) {
  return <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{paths[name]}</svg>;
}
const statusLabels:Record<string,string>={available:'Sẵn sàng',completed:'Hoàn thành',allow:'Cho phép',measured:'Đã đo thực tế',unverified:'Chưa kiểm tra',configured_unverified:'Đã cấu hình',unavailable:'Chưa sẵn sàng',failed:'Không thành công',blocked:'Đã ngăn',block:'Ngăn nội dung',degraded:'Có lưu ý',allow_with_warning:'Cho phép kèm lưu ý',skipped:'Bỏ qua',not_started:'Chưa thực hiện',running:'Đang xử lý',extractive:'Trích đoạn nguồn',llm:'LLM có dẫn chứng',clarification:'Cần làm rõ',withheld:'Giữ lại nội dung',not_called:'Chưa gọi',fallback:'Phương án dự phòng',request_clarification:'Cần làm rõ',escalate:'Cần hỗ trợ y tế'};
export function Badge({value}:{value:string}) {return <span className={`badge ${value.toLowerCase()}`} title={value}><i/>{statusLabels[value.toLowerCase()] || value.replaceAll('_',' ')}</span>;}
export const agentInfo=[
  {id:'prediction',name:'Prediction',label:'Dự đoán',icon:'activity',description:'Chạy MLP với dữ liệu mô phỏng.'},
  {id:'knowledge',name:'Knowledge',label:'Truy hồi',icon:'book',description:'Tìm evidence trong Neo4j/RAG.'},
  {id:'rl',name:'RL decision',label:'Đề xuất giáo dục',icon:'chart',description:'Chọn hành động từ policy giáo dục.'},
  {id:'education',name:'Education',label:'Giải thích',icon:'chat',description:'Soạn câu trả lời từ nguồn đã lấy.'},
  {id:'verifier',name:'Verifier',label:'Kiểm chứng',icon:'search',description:'Kiểm tra từng claim và trích dẫn.'},
  {id:'safety',name:'Safety',label:'An toàn',icon:'shield',description:'Kiểm tra đầu vào và trước công bố.'},
] as const;
export function SectionTitle({eyebrow,title,children}:{eyebrow?:string;title:string;children?:ReactNode}) {return <div className="section-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>{children}</div>;}
