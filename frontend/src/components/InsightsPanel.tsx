import React from 'react';
import type { DirectMessage, DriftSummary } from '../types';
import { Activity, MessageSquareWarning, PieChart } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface InsightsPanelProps {
  dms: DirectMessage[];
  driftSummary: DriftSummary | null;
}

export function InsightsPanel({ dms, driftSummary }: InsightsPanelProps) {
  return (
    <aside style={{ width: 280, display: 'flex', flexDirection: 'column', gap: 24, flexShrink: 0, overflowY: 'auto', paddingBottom: 64 }} className="scrollbar-hide">
      
      {/* Drift Score */}
      <div className="glass-panel" style={{ padding: '24px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        
        <div style={{ display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h3 className="font-display" style={{ fontSize: 12, fontWeight: 500, letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
            System Entropy
          </h3>
          <PieChart size={14} color="var(--text-muted)" />
        </div>

        <div style={{ position: 'relative', width: 140, height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          
          <svg style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)', position: 'absolute' }} viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="46" fill="transparent" stroke="var(--surface-active)" strokeWidth="4" />
            <motion.circle 
              className="progress-ring__circle" 
              cx="50" cy="50" r="46" 
              fill="transparent" 
              stroke="var(--text-primary)" 
              strokeWidth="4"
              strokeDasharray="289"
              initial={{ strokeDashoffset: 289 }}
              animate={{ strokeDashoffset: driftSummary ? 289 - (289 * (driftSummary.drift_score / 100)) : 289 }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </svg>
          
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span className="font-display" style={{ fontSize: 32, fontWeight: 600, color: 'var(--text-primary)' }}>
              {driftSummary ? `${driftSummary.drift_score}%` : '--'}
            </span>
          </div>
        </div>

        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          key={driftSummary ? driftSummary.drift_label : 'empty'}
          className="font-mono" 
          style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 24, display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Activity size={12} />
          {driftSummary ? driftSummary.drift_label : 'Awaiting data'}
        </motion.p>
      </div>

      {/* DMs Panel */}
      <div className="glass-panel" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <h3 className="font-display" style={{ fontSize: 12, fontWeight: 500, letterSpacing: '0.05em', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
          <MessageSquareWarning size={14} /> DMs
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <AnimatePresence>
            {dms.length === 0 ? (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ padding: '16px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                No active comms
              </motion.div>
            ) : (
              dms.map((dm, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  style={{ background: 'var(--surface-active)', padding: 12, borderRadius: 6, border: '1px solid var(--border-color)' }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, alignItems: 'center' }}>
                    <span className="font-display" style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>@{dm.persona_name}</span>
                    <span className="font-mono" style={{ fontSize: 10, color: 'var(--text-muted)' }}>Hop {dm.hop}</span>
                  </div>
                  <p className="font-body" style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>"{dm.text}"</p>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>
    </aside>
  );
}
