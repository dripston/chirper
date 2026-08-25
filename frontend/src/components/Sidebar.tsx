import { Home, Search, Bell, Mail, User, Cpu, Network } from 'lucide-react';

interface SidebarProps {
  activePersonaId: string | null;
  notificationCount: number;
}

export function Sidebar({ activePersonaId, notificationCount }: SidebarProps) {
  return (
    <aside style={{ width: 275, padding: '12px 24px', display: 'flex', flexDirection: 'column', gap: 8, height: '100vh', position: 'sticky', top: 0 }}>
      {/* Logo */}
      <div style={{ padding: '12px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12, color: 'var(--text-primary)' }}>
        <Network size={32} color="var(--accent-primary)" />
        <span className="font-display" style={{ fontSize: 24, fontWeight: 800 }}>Chirper</span>
      </div>

      {/* Nav Links */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '12px', color: 'var(--text-primary)', textDecoration: 'none', borderRadius: 9999, transition: 'background 0.2s', fontSize: 20, fontWeight: 700 }}>
          <Home size={28} /> Home
        </a>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '12px', color: 'var(--text-primary)', textDecoration: 'none', borderRadius: 9999, transition: 'background 0.2s', fontSize: 20 }}>
          <Search size={28} /> Explore
        </a>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '12px', color: 'var(--text-primary)', textDecoration: 'none', borderRadius: 9999, transition: 'background 0.2s', fontSize: 20, position: 'relative' }}>
          <div style={{ position: 'relative' }}>
            <Bell size={28} />
            {notificationCount > 0 && (
              <div style={{ position: 'absolute', top: -2, right: -2, background: 'var(--accent-error)', color: 'white', fontSize: 10, fontWeight: 700, minWidth: 16, height: 16, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid var(--bg-color)', padding: '0 4px' }}>
                {notificationCount}
              </div>
            )}
          </div>
          Notifications
        </a>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '12px', color: 'var(--text-primary)', textDecoration: 'none', borderRadius: 9999, transition: 'background 0.2s', fontSize: 20 }}>
          <Mail size={28} /> Messages
        </a>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '12px', color: 'var(--text-primary)', textDecoration: 'none', borderRadius: 9999, transition: 'background 0.2s', fontSize: 20 }}>
          <User size={28} /> Profile
        </a>
      </nav>

      {/* Post Button */}
      <button className="btn-primary" style={{ marginTop: 16, padding: '16px', fontSize: 17, width: '100%', boxShadow: 'rgba(255, 255, 255, 0.2) 0px 0px 15px, rgba(255, 255, 255, 0.15) 0px 0px 3px 1px' }}>
        Post
      </button>

      {/* Active Persona indicator (debug) */}
      {activePersonaId && (
        <div style={{ marginTop: 'auto', padding: 16, background: 'var(--surface-active)', borderRadius: 16, border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Cpu size={20} color="var(--accent-primary)" />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span className="font-body" style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Thinking...</span>
              <span className="font-mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{activePersonaId}</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
