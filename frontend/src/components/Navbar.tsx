
import { Search, Bell, MessageSquare, User } from 'lucide-react';

export function Navbar() {
  return (
    <header style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      height: 48,
      background: 'rgba(0,0,0,0.8)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      zIndex: 50
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '25%' }}>
        <span className="material-symbols-outlined" style={{ fontSize: 20, color: 'var(--text-primary)' }}>hub</span>
        <h1 className="font-display" style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0' }}>
          Chirper
        </h1>
        <span className="font-mono" style={{ fontSize: 10, color: 'var(--text-muted)', background: 'var(--surface-active)', padding: '2px 6px', borderRadius: 4, marginLeft: 8 }}>BETA</span>
      </div>

      {/* Search */}
      <div style={{ flex: 1, maxWidth: 400, display: 'flex', justifyContent: 'center' }}>
        <div style={{ position: 'relative', width: '100%', display: 'flex', alignItems: 'center' }}>
          <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: 10 }} />
          <input 
            type="text" 
            placeholder="Search..." 
            className="input-minimal font-body"
            style={{
              padding: '6px 12px 6px 32px',
              borderRadius: 6,
              background: 'var(--surface)',
              border: '1px solid var(--border-color)',
              fontSize: 13,
              transition: 'border-color 0.15s ease'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = 'var(--text-secondary)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'var(--border-color)';
            }}
          />
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4, width: '25%' }}>
        <button className="btn" style={{ padding: 6 }}><Bell size={16} /></button>
        <button className="btn" style={{ padding: 6 }}><MessageSquare size={16} /></button>
        <button className="btn" style={{ padding: 4, borderRadius: '50%', marginLeft: 8 }}>
          <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--surface-active)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border-color)' }}>
            <User size={14} color="var(--text-secondary)" />
          </div>
        </button>
      </div>
    </header>
  );
}
