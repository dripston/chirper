import type { PostReaction } from '../types';
import { MessageCircle, Repeat2, Heart, BarChart2, Share, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';
import { VerifiedBadge } from './VerifiedBadge';

interface PostCardProps {
  post: PostReaction;
}

export function PostCard({ post }: PostCardProps) {
  const isRepost = post.action === 'repost';
  const isArgue = post.action === 'argue';
  const isComment = post.action === 'comment';

  // Format action text
  let actionText = '';
  if (isRepost) {
    actionText = `${post.persona_name} reposted`;
  } else if (isArgue) {
    actionText = `${post.persona_name} quoted`;
  }

  // Fallback avatar handling
  const avatarUrl = `/avatars/${post.persona_id}.jpg`;

  return (
    <motion.article 
      layout
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="x-post"
      style={{ display: 'flex', flexDirection: 'column', gap: 4 }}
    >
      {/* Top Action Label (e.g. User Reposted) */}
      {(isRepost || isArgue) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 36, marginBottom: 4 }}>
          {isRepost ? <Repeat2 size={14} color="var(--text-secondary)" /> : <ShieldAlert size={14} color="var(--text-secondary)" />}
          <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 700 }}>
            {actionText}
          </span>
        </div>
      )}

      <div style={{ display: 'flex', gap: 12 }}>
        {/* Left Column: Avatar */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <img 
            src={avatarUrl} 
            alt={post.persona_name} 
            className="x-avatar"
            onError={(e) => {
              // Fallback if image fails to load
              e.currentTarget.style.display = 'none';
              if (e.currentTarget.nextElementSibling) {
                (e.currentTarget.nextElementSibling as HTMLElement).style.display = 'flex';
              }
            }}
          />
          {/* Fallback circle */}
          <div className="x-avatar" style={{ display: 'none', background: 'var(--accent-primary)', color: 'white', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
            {post.persona_name.charAt(0).toUpperCase()}
          </div>
          
          {/* Vertical line for threaded comments */}
          {isComment && (
            <div style={{ width: 2, flex: 1, background: 'var(--border-color)', marginTop: 4, marginBottom: -12 }} />
          )}
        </div>

        {/* Right Column: Content */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span className="font-body" style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>
              {post.persona_name}
            </span>
            <VerifiedBadge />
            <span style={{ color: 'var(--text-secondary)', fontSize: 15 }}>@{post.persona_id}</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: 15 }}>·</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: 15, textDecoration: 'hover:underline' }}>{post.hop}h</span>
          </div>

          {/* Replying to... */}
          {isComment && (
            <div style={{ fontSize: 15, color: 'var(--text-secondary)', marginTop: -2, marginBottom: 4 }}>
              Replying to <span style={{ color: 'var(--accent-primary)' }}>@original</span>
            </div>
          )}

          {/* Text Content */}
          <p className="font-body" style={{ fontSize: 15, lineHeight: 1.5, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
            {post.text}
          </p>

          {/* Quote Tweet Box (for Reposts) */}
          {isRepost && (
            <div style={{ marginTop: 12, padding: 12, border: '1px solid var(--border-color)', borderRadius: 16, cursor: 'pointer', transition: 'background 0.2s' }} className="hover:bg-[var(--surface-active)]">
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
                <span className="font-body" style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>Original Poster</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: 15 }}>@original</span>
              </div>
              <p className="font-body" style={{ fontSize: 15, color: 'var(--text-primary)' }}>
                [Content quoted from previous hop in thread...]
              </p>
            </div>
          )}

          {/* Action Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, maxWidth: 425 }}>
            <button className="x-icon-btn group" style={{ color: 'var(--text-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ padding: 8, borderRadius: '50%', transition: '0.2s' }} className="hover:bg-[rgba(29,155,240,0.1)] hover:text-[#1d9bf0]">
                  <MessageCircle size={18.5} />
                </div>
                <span style={{ fontSize: 13, transition: '0.2s' }} className="hover:text-[#1d9bf0]">
                  {Math.floor(Math.random() * 50) + 1}
                </span>
              </div>
            </button>
            
            <button className="x-icon-btn group" style={{ color: 'var(--text-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ padding: 8, borderRadius: '50%', transition: '0.2s' }} className="hover:bg-[rgba(0,186,124,0.1)] hover:text-[#00ba7c]">
                  <Repeat2 size={18.5} />
                </div>
                <span style={{ fontSize: 13, transition: '0.2s' }} className="hover:text-[#00ba7c]">
                  {Math.floor(Math.random() * 200) + 10}
                </span>
              </div>
            </button>

            <button className="x-icon-btn group" style={{ color: 'var(--text-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ padding: 8, borderRadius: '50%', transition: '0.2s' }} className="hover:bg-[rgba(249,24,128,0.1)] hover:text-[#f91880]">
                  <Heart size={18.5} />
                </div>
                <span style={{ fontSize: 13, transition: '0.2s' }} className="hover:text-[#f91880]">
                  {Math.floor(Math.random() * 900) + 100}
                </span>
              </div>
            </button>

            <button className="x-icon-btn group" style={{ color: 'var(--text-secondary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <div style={{ padding: 8, borderRadius: '50%', transition: '0.2s' }} className="hover:bg-[rgba(29,155,240,0.1)] hover:text-[#1d9bf0]">
                  <BarChart2 size={18.5} />
                </div>
                <span style={{ fontSize: 13, transition: '0.2s' }} className="hover:text-[#1d9bf0]">
                  {(Math.random() * 10).toFixed(1)}K
                </span>
              </div>
            </button>

            <div style={{ display: 'flex' }}>
              <button className="x-icon-btn" style={{ padding: 8, borderRadius: '50%', transition: '0.2s' }}><Share size={18.5} /></button>
            </div>
          </div>
        </div>
      </div>
    </motion.article>
  );
}
