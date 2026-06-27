import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileText, Upload, LogOut, Settings, Bell, Search } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { cn } from '../utils/cn';

const NavItem = ({ to, icon: Icon, children, active }) => (
  <Link
    to={to}
    className={cn(
      "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
      active 
        ? "bg-primary text-white shadow-lg shadow-primary/20" 
        : "text-muted-foreground hover:bg-secondary hover:text-white"
    )}
  >
    <Icon size={20} className={active ? "text-white" : "group-hover:text-white"} />
    <span className="font-medium">{children}</span>
  </Link>
);

const DashboardLayout = () => {
  const { logout, user } = useAuthStore();
  const location = useLocation();

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card/50 backdrop-blur-xl flex flex-col p-6">
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-white fill-current">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="text-xl font-bold tracking-tight">AnomalyAI</span>
        </div>

        <nav className="flex-1 space-y-2">
          <NavItem to="/" icon={LayoutDashboard} active={location.pathname === '/'}>Dashboard</NavItem>
          <NavItem to="/logs" icon={FileText} active={location.pathname === '/logs'}>Log Explorer</NavItem>
          <NavItem to="/ingestion" icon={Upload} active={location.pathname === '/ingestion'}>Ingestion</NavItem>
        </nav>

        <div className="pt-6 border-t border-border mt-auto">
          <button 
            onClick={logout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all w-full text-left"
          >
            <LogOut size={20} />
            <span className="font-medium">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-border bg-card/30 backdrop-blur-xl flex items-center justify-between px-8">
          <div className="flex items-center gap-4 bg-secondary/50 px-4 py-2 rounded-xl border border-border w-96 group focus-within:ring-2 ring-primary/20">
            <Search size={18} className="text-muted-foreground group-focus-within:text-primary" />
            <input 
              type="text" 
              placeholder="Search logs, services, or anomalies..." 
              className="bg-transparent border-none outline-none text-sm w-full"
            />
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2 rounded-lg hover:bg-secondary text-muted-foreground transition-colors relative">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-destructive rounded-full border-2 border-background"></span>
            </button>
            <div className="h-8 w-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-primary font-bold">
              {user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
