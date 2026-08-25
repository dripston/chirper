import { useState } from 'react';
import type { PostReaction } from '../types';
import { PostCard } from './PostCard';
import { Image, FileType, Smile, Calendar, MapPin, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FeedProps {
  onStartSimulation: (text: string, driftTarget: number | null, maxHops: number, timeLimit: number) => void;
  feed: PostReaction[];
  isStreaming: boolean;
  originalText: string;
  errorMsg: string | null;
  finalText: string | null;
}

export function Feed({ onStartSimulation, feed, isStreaming, originalText, errorMsg, finalText }: FeedProps) {
  const [inputText, setInputText] = useState('');
  
  // Settings
  const [driftTarget, setDriftTarget] = useState<number | ''>('');
  const [maxHops, setMaxHops] = useState(15);
  const [timeLimit, setTimeLimit] = useState(60);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onStartSimulation(
      inputText, 
      typeof driftTarget === 'number' ? driftTarget : null,
      maxHops,
      timeLimit
    );
    setInputText('');
  };

  return (
    <main className="x-feed-container scrollbar-hide" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
      
      {/* Header */}
      <header style={{ position: 'sticky', top: 0, zIndex: 10, background: 'rgba(0, 0, 0, 0.65)', backdropFilter: 'blur(12px)', borderBottom: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column' }}>
        <h1 className="font-body" style={{ padding: '16px', fontSize: 20, fontWeight: 700 }}>For you</h1>
        <div style={{ display: 'flex' }}>
          <div style={{ flex: 1, padding: '16px', textAlign: 'center', fontWeight: 700, borderBottom: '4px solid var(--accent-primary)', color: 'var(--text-primary)' }}>For you</div>
          <div style={{ flex: 1, padding: '16px', textAlign: 'center', fontWeight: 500, color: 'var(--text-secondary)' }}>Following</div>
        </div>
      </header>

      {/* Composer */}
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)', display: 'flex', gap: 12 }}>
        <div className="x-avatar" style={{ background: 'var(--accent-primary)' }} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column' }}>
            <textarea 
              placeholder="What is happening?!"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={isStreaming}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', fontSize: 20, resize: 'none', minHeight: 52, padding: '12px 0', fontFamily: 'inherit' }}
            />
            
            {/* Quick Settings Bar in Composer */}
            <div style={{ display: 'flex', gap: 12, paddingBottom: 12, borderBottom: '1px solid var(--border-color)', marginBottom: 12 }}>
              <input type="number" placeholder="Drift %" value={driftTarget} onChange={e => setDriftTarget(e.target.value ? parseInt(e.target.value) : '')} style={{ width: 80, background: 'transparent', border: 'none', color: 'var(--accent-primary)', fontSize: 13, outline: 'none' }} />
              <input type="number" placeholder="Max Hops" value={maxHops} onChange={e => setMaxHops(parseInt(e.target.value))} style={{ width: 80, background: 'transparent', border: 'none', color: 'var(--accent-primary)', fontSize: 13, outline: 'none' }} />
              <input type="number" placeholder="Time (s)" value={timeLimit} onChange={e => setTimeLimit(parseInt(e.target.value))} style={{ width: 80, background: 'transparent', border: 'none', color: 'var(--accent-primary)', fontSize: 13, outline: 'none' }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 4, marginLeft: -8 }}>
                <button type="button" className="x-icon-btn"><Image size={20} /></button>
                <button type="button" className="x-icon-btn"><FileType size={20} /></button>
                <button type="button" className="x-icon-btn"><Smile size={20} /></button>
                <button type="button" className="x-icon-btn"><Calendar size={20} /></button>
                <button type="button" className="x-icon-btn"><MapPin size={20} opacity={0.5} /></button>
              </div>
              <button type="submit" className="btn-primary" disabled={isStreaming || !inputText.trim()}>
                {isStreaming ? 'Posting...' : 'Post'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {errorMsg && (
        <div style={{ padding: '12px 16px', background: 'rgba(244, 33, 46, 0.1)', borderBottom: '1px solid var(--border-color)', color: 'var(--accent-error)', fontSize: 14 }}>
          {errorMsg}
        </div>
      )}

      {/* Show new posts pill */}
      {feed.length > 0 && (
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)', textAlign: 'center', color: 'var(--accent-primary)', cursor: 'pointer', transition: 'background 0.2s' }} className="font-body hover:bg-[var(--surface-hover)]">
          Show {feed.length} posts
        </div>
      )}

      {/* Seed Post */}
      {originalText && (
        <div className="x-post" style={{ borderBottom: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <div className="x-avatar" style={{ background: 'var(--accent-primary)' }} />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span className="font-body" style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>SEED POST</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: 15 }}>@original</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: 15 }}>·</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: 15 }}>1m</span>
              </div>
              <p className="font-body" style={{ fontSize: 15, lineHeight: 1.5, marginTop: 4, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                {originalText}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Feed Stream */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <AnimatePresence initial={false}>
          {feed.map((post, i) => (
            <PostCard key={i} post={post} />
          ))}
        </AnimatePresence>

        {isStreaming && (
          <div style={{ padding: '24px', display: 'flex', justifyContent: 'center' }}>
            <Loader2 className="animate-spin" color="var(--accent-primary)" />
          </div>
        )}

        {/* Final Mutation - Treat like a massive quote tweet / final event */}
        {!isStreaming && finalText && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="x-post"
            style={{ background: 'rgba(29, 155, 240, 0.05)', borderTop: '2px solid var(--accent-primary)' }}
          >
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="x-avatar" style={{ background: 'var(--accent-error)' }} />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span className="font-body" style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>FINAL MUTATION</span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: 15 }}>@chirper_system</span>
                </div>
                <p className="font-body" style={{ fontSize: 15, lineHeight: 1.5, marginTop: 4, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                  {finalText}
                </p>
                <div style={{ marginTop: 12, padding: 12, border: '1px solid var(--border-color)', borderRadius: 16 }}>
                  <span style={{ fontWeight: 700, fontSize: 15 }}>Original Seed</span><br/>
                  <span style={{ color: 'var(--text-secondary)' }}>{originalText}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </main>
  );
}
