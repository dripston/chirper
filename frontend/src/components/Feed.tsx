import React, { useState } from 'react';
import type { PostReaction } from '../types';
import { PostCard } from './PostCard';
import { Send, Image, Link } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FeedProps {
  onStartSimulation: (text: string) => void;
  feed: PostReaction[];
  isStreaming: boolean;
  originalText: string;
}

export function Feed({ onStartSimulation, feed, isStreaming, originalText }: FeedProps) {
  const [inputText, setInputText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onStartSimulation(inputText);
    setInputText('');
  };

  return (
    <main style={{ flex: 1, maxWidth: 680, display: 'flex', flexDirection: 'column', gap: 24, overflowY: 'auto', paddingBottom: 64 }} className="scrollbar-hide">
      
      {/* Input Area */}
      <form onSubmit={handleSubmit} className="glass-panel" style={{ padding: '16px', display: 'flex', gap: 12, alignItems: 'center' }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', background: 'var(--surface-active)', borderRadius: 6, padding: '8px 12px', border: '1px solid var(--border-color)' }}>
          <input 
            type="text" 
            placeholder="Initialize simulation..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isStreaming}
            className="input-minimal"
          />
        </div>
        <button type="button" className="btn" style={{ padding: 8, border: '1px solid var(--border-color)' }}><Image size={16} /></button>
        <button type="button" className="btn" style={{ padding: 8, border: '1px solid var(--border-color)' }}><Link size={16} /></button>
        <button type="submit" className="btn btn-primary" disabled={isStreaming || !inputText.trim()} style={{ padding: '8px 16px' }}>
          {isStreaming ? 'Running...' : 'Launch'} <Send size={14} />
        </button>
      </form>

      {/* Seed Post */}
      <AnimatePresence>
        {originalText && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel" 
            style={{ padding: '20px 24px', borderLeft: '2px solid var(--text-secondary)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span className="font-display" style={{ color: 'var(--text-secondary)', fontSize: 11, fontWeight: 500, letterSpacing: '0.05em', textTransform: 'uppercase' }}>SEED</span>
            </div>
            <p className="font-body" style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--text-primary)' }}>{originalText}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Feed Stream */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <AnimatePresence mode="popLayout">
          {feed.map((post, i) => (
            <PostCard key={i} post={post} />
          ))}
        </AnimatePresence>

        {isStreaming && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="skeleton" 
            style={{ height: 120 }} 
          />
        )}
      </div>
    </main>
  );
}
