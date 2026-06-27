import { useQuery } from '@tanstack/react-query';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts';
import { Activity, AlertTriangle, Database, TrendingUp, Clock } from 'lucide-react';
import api from '../services/api';
import { cn } from '../utils/cn';

const StatCard = ({ title, value, icon: Icon, description, trend, color }) => (
  <div className="glass p-6 rounded-2xl border border-white/5 bg-card/40 relative overflow-hidden group hover:bg-card/60 transition-all duration-300">
    <div className={cn("absolute top-0 right-0 w-24 h-24 blur-[60px] opacity-20 rounded-full", color)} />
    <div className="flex items-center justify-between mb-4">
      <div className={cn("p-3 rounded-xl", color.replace('bg-', 'bg-opacity-20 text-'))}>
        <Icon size={24} />
      </div>
      {trend && (
        <span className={cn("text-xs font-medium px-2 py-1 rounded-lg", trend > 0 ? "bg-emerald-500/10 text-emerald-500" : "bg-destructive/10 text-destructive")}>
          {trend > 0 ? '+' : ''}{trend}%
        </span>
      )}
    </div>
    <div className="space-y-1">
      <h3 className="text-muted-foreground text-sm font-medium">{title}</h3>
      <div className="text-3xl font-bold tracking-tight">{value}</div>
      <p className="text-xs text-muted-foreground mt-2">{description}</p>
    </div>
  </div>
);

const Dashboard = () => {
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/summary');
      return data;
    },
    refetchInterval: 10000,
  });

  const { data: recent, isLoading: loadingRecent } = useQuery({
    queryKey: ['dashboard-recent'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/recent?limit=5');
      return data;
    },
    refetchInterval: 10000,
  });

  const { data: trends, isLoading: loadingTrends } = useQuery({
    queryKey: ['dashboard-trends'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/trends');
      return data;
    },
  });

  if (loadingSummary || loadingRecent || loadingTrends) {
    return (
      <div className="animate-pulse space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => <div key={i} className="h-40 bg-card/40 rounded-2xl border border-white/5" />)}
        </div>
        <div className="h-96 bg-card/40 rounded-2xl border border-white/5" />
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Overview</h1>
        <p className="text-muted-foreground">Real-time log telemetry and anomaly analysis</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Total Logs" 
          value={summary?.total_logs?.toLocaleString() || '0'} 
          icon={Database}
          description="Total processed log entries"
          color="bg-primary"
        />
        <StatCard 
          title="Anomalies Detected" 
          value={summary?.anomaly_count || '0'} 
          icon={AlertTriangle}
          description="Potentially malicious or erroneous events"
          color="bg-destructive"
        />
        <StatCard 
          title="Anomaly Rate" 
          value={`${summary?.anomaly_percentage || '0'}%`} 
          icon={Activity}
          description="Percentage of anomalous logs"
          color="bg-amber-500"
        />
      </div>

      {/* Main Graph Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass rounded-2xl p-6 border border-white/5 bg-card/40">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2">
              <TrendingUp size={20} className="text-primary" />
              <h3 className="font-semibold text-lg">Anomaly Trends</h3>
            </div>
            <select className="bg-secondary/50 border border-border rounded-lg px-3 py-1.5 text-xs text-muted-foreground outline-none focus:ring-1 ring-primary/30">
              <option>Last 7 Days</option>
              <option>Last 24 Hours</option>
            </select>
          </div>
          
          <div className="h-80 w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f2937" />
                <XAxis 
                  dataKey="date" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#6b7280', fontSize: 12 }} 
                  dy={10}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#6b7280', fontSize: 12 }} 
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '12px' }}
                  itemStyle={{ color: '#3B82F6' }}
                />
                <Area type="monotone" dataKey="count" stroke="#3B82F6" fillOpacity={1} fill="url(#colorCount)" strokeWidth={3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Anomalies Side Table */}
        <div className="glass rounded-2xl p-6 border border-white/5 bg-card/40 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Clock size={20} className="text-destructive" />
              <h3 className="font-semibold text-lg">Live Feed</h3>
            </div>
            <button className="text-xs text-primary hover:underline">View All</button>
          </div>

          <div className="flex-1 space-y-4">
            {recent?.map((log, idx) => (
              <div key={idx} className="flex gap-4 p-3 rounded-xl bg-secondary/20 border border-white/5 hover:bg-secondary/30 transition-colors group">
                <div className={cn(
                  "w-1.5 rounded-full", 
                  log.is_anomaly ? "bg-destructive shadow-[0_0_8px_rgba(239,68,68,0.5)]" : "bg-emerald-500"
                )} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-muted-foreground truncate max-w-[100px]">{log.service}</span>
                    <span className="text-[10px] text-muted-foreground">Just now</span>
                  </div>
                  <p className="text-sm text-foreground truncate group-hover:text-clip group-hover:whitespace-normal transition-all">{log.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
