import React from 'react';
import type { PostReaction } from '../types';
import { MessageCircle, Repeat2, ArrowUpToLine, ArrowDownToLine, MoreHorizontal, ShieldAlert, Cpu } from 'lucide-react';
import { motion } from 'framer-motion';

interface PostCardProps {
  post: PostReaction;
}

export function PostCard({ post }: PostCardProps) {
  const isRepost = post.action === 'repost';
  const isArgue = post.action === 'argue';

  let icon = <Cpu size={14} color="var(--text-muted)" />;
  let badgeLabel = '';
  let badgeColor = 'var(--text-muted)';
  
  if (isRepost) {
    icon = <Repeat2 size={14} color="var(--text-secondary)" />;
    badgeLabel = 'REPOST';
    badgeColor = 'var(--text-primary)';
  } else if (isArgue) {
    icon = <ShieldAlert size={14} color="var(--text-secondary)" />;
    badgeLabel = 'ARGUMENT';
    badgeColor = 'var(--text-primary)';
  }

  return (
    <motion.article 
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
      className="glass-panel glass-panel-hover"
      style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}
    >
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ 
            width: 32, height: 32, borderRadius: '50%', 
            background: 'var(--surface-active)', 
            display: 'flex', alignItems: 'center', justifyContent: 'center', 
            border: '1px solid var(--border-color)'
          }}>
            {icon}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="font-body" style={{ fontWeight: 500, color: 'var(--text-primary)', fontSize: 14 }}>
              {post.persona_name}
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>·</span>
            <span className="font-mono" style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
              Hop {post.hop}
            </span>
          </div>
        </div>
        
        {badgeLabel && (
          <span className="font-display" style={{ 
            padding: '2px 6px', borderRadius: 4, 
            background: 'var(--surface-active)', color: badgeColor, 
            fontSize: 10, fontWeight: 500, letterSpacing: '0.05em', 
            border: '1px solid var(--border-color)' 
          }}>
            {badgeLabel}
          </span>
        )}
      </header>

      <div style={{ paddingLeft: 44 }}>
        <p className="font-body" style={{ 
          fontSize: 14, lineHeight: 1.6, color: 'var(--text-primary)'
        }}>
          {post.text}
        </p>
      </div>

      <footer style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4, paddingLeft: 44 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <button className="btn" style={{ padding: '4px 6px' }}><ArrowUpToLine size={14} /></button>
          <span className="font-mono" style={{ fontSize: 12, padding: '0 4px', color: 'var(--text-secondary)' }}>{(Math.random() * 10).toFixed(1)}k</span>
          <button className="btn" style={{ padding: '4px 6px' }}><ArrowDownToLine size={14} /></button>
        </div>
        
        <button className="btn" style={{ padding: '4px 8px' }}>
          <MessageCircle size={14} /> <span style={{fontSize: 12}}>Reply</span>
        </button>
        <button className="btn" style={{ padding: '4px 8px' }}>
          <Repeat2 size={14} /> <span style={{fontSize: 12}}>Share</span>
        </button>
        <button className="btn" style={{ marginLeft: 'auto', padding: '4px 8px' }}>
          <MoreHorizontal size={14} />
        </button>
      </footer>
    </motion.article>
  );
}
