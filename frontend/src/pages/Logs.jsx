import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, ChevronLeft, ChevronRight, Eye, BrainCircuit, AlertCircle, CheckCircle2, MoreHorizontal } from 'lucide-react';
import api from '../services/api';
import { cn } from '../utils/cn';

const StatusBadge = ({ isAnomaly }) => (
  <div className={cn(
    "px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 w-fit",
    isAnomaly 
      ? "bg-destructive/10 text-destructive border border-destructive/20 animate-pulse" 
      : "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
  )}>
    {isAnomaly ? <AlertCircle size={10} /> : <CheckCircle2 size={10} />}
    {isAnomaly ? 'Anomaly' : 'Normal'}
  </div>
);

const LogTable = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterService, setFilterService] = useState('All');
  const [selectedLog, setSelectedLog] = useState(null);

  const { data: logs, isLoading } = useQuery({
    queryKey: ['logs-explorer'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/recent?limit=100');
      return data;
    },
    refetchInterval: 10000,
  });

  const services = useMemo(() => {
    if (!logs) return ['All'];
    return ['All', ...new Set(logs.map(l => l.service_name))];
  }, [logs]);

  const filteredLogs = useMemo(() => {
    if (!logs) return [];
    return logs.filter(log => {
      const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase()) || 
                           log.service_name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesService = filterService === 'All' || log.service_name === filterService;
      return matchesSearch && matchesService;
    });
  }, [logs, searchTerm, filterService]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Log Explorer</h1>
          <p className="text-muted-foreground">Investigate system events and AI-detected anomalies</p>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={16} />
            <input 
              type="text" 
              placeholder="Search logs..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-secondary/40 border border-border rounded-xl pl-10 pr-4 py-2 text-sm w-64 focus:outline-none focus:ring-2 ring-primary/20 transition-all"
            />
          </div>
          <select 
            value={filterService}
            onChange={(e) => setFilterService(e.target.value)}
            className="bg-secondary/40 border border-border rounded-xl px-4 py-2 text-sm text-muted-foreground focus:outline-none focus:ring-2 ring-primary/20 outline-none"
          >
            {services.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div className="glass rounded-2xl border border-white/5 overflow-hidden bg-card/20">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5 bg-white/5 text-xs text-muted-foreground uppercase tracking-widest font-bold">
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Service</th>
                <th className="px-6 py-4">Log Message</th>
                <th className="px-6 py-4">Score</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                [1,2,3,4,5].map(i => (
                  <tr key={i} className="animate-pulse">
                     <td colSpan="6" className="px-6 py-4"><div className="h-4 bg-white/10 rounded w-full" /></td>
                  </tr>
                ))
              ) : filteredLogs.map((log, idx) => (
                <tr key={idx} className="hover:bg-white/5 transition-colors group">
                  <td className="px-6 py-4 text-xs font-mono text-muted-foreground">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs font-semibold px-2 py-1 bg-secondary/50 rounded-lg border border-white/5">{log.service_name}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap items-center gap-2 max-w-xl">
                      <p className="text-sm truncate group-hover:text-clip group-hover:whitespace-normal">{log.message}</p>
                      {log.trace_id && (
                        <span className="text-[9px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1.5 py-0.5 rounded font-mono shrink-0 select-all" title={`Trace ID: ${log.trace_id}`}>
                          otel-trace: {log.trace_id.substring(0, 8)}...
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-xs font-mono font-bold text-primary">
                    {(log.anomaly_score * 10).toFixed(2)}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge isAnomaly={log.is_anomaly} />
                  </td>
                  <td className="px-6 py-4">
                    <button 
                      onClick={() => setSelectedLog(log)}
                      className="p-2 rounded-lg hover:bg-primary/20 text-primary transition-all flex items-center gap-2 group/btn"
                    >
                      <BrainCircuit size={16} className="group-hover/btn:scale-110 transition-transform" />
                      <span className="text-xs font-bold">Explain</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between bg-white/5">
          <p className="text-xs text-muted-foreground">Showing {filteredLogs.length} entries</p>
          <div className="flex items-center gap-2">
            <button className="p-1 rounded-lg hover:bg-white/10 disabled:opacity-30" disabled><ChevronLeft size={18} /></button>
            <button className="p-1 rounded-lg hover:bg-white/10 disabled:opacity-30" disabled><ChevronRight size={18} /></button>
          </div>
        </div>
      </div>

      {/* Explanation Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="glass w-full max-w-2xl rounded-2xl border border-white/10 shadow-2xl bg-card overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/5">
              <div className="flex items-center gap-2">
                <BrainCircuit className="text-primary" size={20} />
                <h3 className="font-bold">AI Explanation</h3>
              </div>
              <button onClick={() => setSelectedLog(null)} className="text-muted-foreground hover:text-white transition-colors">&times;</button>
            </div>
            <div className="p-8 space-y-6">
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Original Log</h4>
                <div className="p-4 rounded-xl bg-[#0d1117] border border-white/5 font-mono text-sm break-all">
                  {selectedLog.message}
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Analysis Result</h4>
                <div className="p-6 rounded-xl bg-primary/5 border border-primary/20 transition-all">
                  <p className="text-blue-100 leading-relaxed italic">
                    {selectedLog.simplified_message || "This log appears to be within normal operating parameters. No structural anomalies were detected."}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-secondary/20 border border-white/5">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold mb-1">Anomaly Probability</p>
                  <p className="text-xl font-bold text-primary">{(selectedLog.anomaly_score * 100).toFixed(1)}%</p>
                </div>
                <div className="p-4 rounded-xl bg-secondary/20 border border-white/5">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold mb-1">Template ID</p>
                  <p className="text-xl font-bold text-foreground">#{selectedLog.parsed_event || 'E0'}</p>
                </div>
              </div>

              {selectedLog.trace_id && (
                <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/10 space-y-2">
                  <p className="text-[10px] text-blue-400 uppercase font-bold tracking-wider">OpenTelemetry Correlation</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
                    <div><span className="text-muted-foreground">Trace ID:</span> <span className="text-blue-200 select-all">{selectedLog.trace_id}</span></div>
                    {selectedLog.span_id && <div><span className="text-muted-foreground">Span ID:</span> <span className="text-blue-200 select-all">{selectedLog.span_id}</span></div>}
                  </div>
                </div>
              )}
            </div>
            <div className="px-6 py-4 border-t border-white/10 bg-white/5 flex justify-end">
              <button 
                onClick={() => setSelectedLog(null)}
                className="bg-primary hover:bg-primary/90 text-white px-6 py-2 rounded-xl text-sm font-bold transition-all"
              >
                Close Analysis
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LogTable;
