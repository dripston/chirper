import React, { useEffect, useState } from 'react';
import type { PersonaSummary } from '../types';
import { Home, TrendingUp, Newspaper, Compass, Plus, Users, Cpu, ShieldAlert, Zap } from 'lucide-react';

export function Sidebar() {
  const [personas, setPersonas] = useState<PersonaSummary[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/personas')
      .then(res => res.json())
      .then(data => setPersonas(data))
      .catch(err => console.error("Failed to load personas:", err));
  }, []);

  const renderIcon = (ideology: string) => {
    switch (ideology) {
      case 'conspiracy': return <ShieldAlert size={14} color="var(--text-secondary)" />;
      case 'engagement': return <Zap size={14} color="var(--text-secondary)" />;
      case 'satirist': return <Users size={14} color="var(--text-secondary)" />;
      default: return <Cpu size={14} color="var(--text-secondary)" />;
    }
  };

  return (
    <aside style={{ width: 220, display: 'flex', flexDirection: 'column', gap: 24, flexShrink: 0, overflowY: 'auto' }} className="scrollbar-hide">
      
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <a href="#" className="btn" style={{ justifyContent: 'flex-start', padding: '8px 12px', background: 'var(--surface)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}>
          <Home size={16} /> Home
        </a>
        <a href="#" className="btn" style={{ justifyContent: 'flex-start', padding: '8px 12px' }}>
          <TrendingUp size={16} /> Popular
        </a>
        <a href="#" className="btn" style={{ justifyContent: 'flex-start', padding: '8px 12px' }}>
          <Newspaper size={16} /> News
        </a>
        <a href="#" className="btn" style={{ justifyContent: 'flex-start', padding: '8px 12px' }}>
          <Compass size={16} /> Explore
        </a>
      </nav>

      <div style={{ height: 1, backgroundColor: 'var(--border-color)' }}></div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <h2 className="font-display" style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.05em', color: 'var(--text-muted)', paddingLeft: 12 }}>
          Personas
        </h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {personas.map(p => (
            <div key={p.id} className="btn" style={{ justifyContent: 'flex-start', padding: '6px 12px', gap: 10 }}>
              <div style={{ width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {renderIcon(p.ideology)}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                <span className="font-body" style={{ fontSize: 13, color: 'var(--text-primary)' }}>{p.name}</span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{p.ideology}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <button className="btn" style={{ marginTop: 'auto', padding: '10px', border: '1px dashed var(--border-color)' }}>
        <Plus size={16} /> New Community
      </button>
    </aside>
  );
}
