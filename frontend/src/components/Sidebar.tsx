import { Home, Search, Bell, Mail, User, Cpu } from 'lucide-react';

interface SidebarProps {
  activePersonaId: string | null;
}

export function Sidebar({ activePersonaId }: SidebarProps) {
  return (
    <aside style={{ width: 275, padding: '12px 24px', display: 'flex', flexDirection: 'column', gap: 8, height: '100vh', position: 'sticky', top: 0 }}>
      {/* Logo */}
      <div style={{ padding: '12px', marginBottom: 16 }}>
        <svg viewBox="0 0 24 24" aria-hidden="true" style={{ width: 32, height: 32, fill: 'var(--text-primary)' }}>
          <g><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 22.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path></g>
        </svg>
      </div>

      {/* Nav Links */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '12px', color: 'var(--text-primary)', textDecoration: 'none', borderRadius: 9999, transition: 'background 0.2s', fontSize: 20, fontWeight: 700 }}>
          <Home size={28} /> Home
        </a>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '12px', color: 'var(--text-primary)', textDecoration: 'none', borderRadius: 9999, transition: 'background 0.2s', fontSize: 20 }}>
          <Search size={28} /> Explore
        </a>
        <a href="#" style={{ display: 'flex', alignItems: 'center', gap: 20, padding: '12px', color: 'var(--text-primary)', textDecoration: 'none', borderRadius: 9999, transition: 'background 0.2s', fontSize: 20 }}>
          <Bell size={28} /> Notifications
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
