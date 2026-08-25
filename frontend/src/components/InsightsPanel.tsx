import type { DirectMessage, DriftSummary } from '../types';
import { Search } from 'lucide-react';

interface InsightsProps {
  dms: DirectMessage[];
  driftSummary: DriftSummary | null;
  liveDrift: { score: number, label: string } | null;
}

export function InsightsPanel({ dms, driftSummary, liveDrift }: InsightsProps) {
  return (
    <aside style={{ width: 350, padding: '12px 24px', display: 'flex', flexDirection: 'column', gap: 16, height: '100vh', position: 'sticky', top: 0 }}>
      {/* Search Bar */}
      <div style={{ position: 'relative' }}>
        <div style={{ position: 'absolute', top: 12, left: 16, color: 'var(--text-secondary)' }}>
          <Search size={18} />
        </div>
        <input 
          type="text" 
          placeholder="Search" 
          style={{ width: '100%', background: 'var(--surface-active)', border: '1px solid transparent', padding: '12px 16px 12px 44px', borderRadius: 9999, color: 'var(--text-primary)', outline: 'none', transition: 'border-color 0.2s, background 0.2s' }}
          onFocus={e => { e.target.style.background = 'var(--bg-color)'; e.target.style.borderColor = 'var(--accent-primary)'; }}
          onBlur={e => { e.target.style.background = 'var(--surface-active)'; e.target.style.borderColor = 'transparent'; }}
        />
      </div>

      {/* Subscribe to Premium */}
      <div className="x-panel" style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <h2 className="font-body" style={{ fontSize: 20, fontWeight: 800 }}>Subscribe to Premium</h2>
        <p className="font-body" style={{ fontSize: 15, lineHeight: 1.3, color: 'var(--text-primary)' }}>
          Subscribe to unlock new features and if eligible, receive a share of ads revenue.
        </p>
        <button className="btn-primary" style={{ alignSelf: 'flex-start', marginTop: 4 }}>Subscribe</button>
      </div>

      {/* What's happening (Live Drift) */}
      <div className="x-panel" style={{ display: 'flex', flexDirection: 'column' }}>
        <h2 className="font-body" style={{ fontSize: 20, fontWeight: 800, padding: '12px 16px' }}>What's happening</h2>
        
        <div className="x-post" style={{ borderBottom: 'none', padding: '12px 16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Simulation Status · Live</span>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>...</span>
          </div>
          <p className="font-body" style={{ fontSize: 15, fontWeight: 700, marginTop: 2, color: 'var(--text-primary)' }}>
            Drift Score: {driftSummary ? driftSummary.drift_score : (liveDrift?.score || 0)}%
          </p>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Trend: {driftSummary ? driftSummary.drift_label : (liveDrift?.label || "Barely changed")}
          </span>
        </div>

        {driftSummary && driftSummary.mvp_distorter && (
          <div className="x-post" style={{ borderBottom: 'none', padding: '12px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Simulation Analytics · MVP</span>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>...</span>
            </div>
            <p className="font-body" style={{ fontSize: 15, fontWeight: 700, marginTop: 2, color: 'var(--text-primary)' }}>
              Top Distorter: @{driftSummary.mvp_distorter}
            </p>
          </div>
        )}
      </div>

      {/* Who to follow (DMs) */}
      <div className="x-panel" style={{ display: 'flex', flexDirection: 'column' }}>
        <h2 className="font-body" style={{ fontSize: 20, fontWeight: 800, padding: '12px 16px' }}>Direct Messages</h2>
        {dms.length === 0 ? (
          <p style={{ padding: '0 16px 16px', fontSize: 14, color: 'var(--text-secondary)' }}>No DMs sent yet.</p>
        ) : (
          dms.map((dm, i) => (
            <div key={i} className="x-post" style={{ borderBottom: i === dms.length - 1 ? 'none' : '1px solid var(--border-color)', display: 'flex', gap: 12 }}>
              <img src={`/avatars/${dm.persona_id}.jpg`} alt="" className="x-avatar" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span className="font-body" style={{ fontWeight: 700, fontSize: 15 }}>{dm.persona_name}</span>
                <span className="font-body" style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{dm.text.substring(0, 60)}...</span>
              </div>
            </div>
          ))
        )}
      </div>

    </aside>
  );
}
