import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileType, Code, Share2, Copy, Check, Terminal, TerminalSquare, Activity, Server, Radio, Wifi } from 'lucide-react';
import { toast } from 'sonner';
import api from '../services/api';
import { cn } from '../utils/cn';

const TabButton = ({ active, onClick, icon: Icon, children }) => (
  <button
    onClick={onClick}
    className={cn(
      "flex items-center gap-2 px-6 py-4 border-b-2 transition-all duration-200 outline-none",
      active 
        ? "border-primary text-primary bg-primary/5" 
        : "border-transparent text-muted-foreground hover:text-white hover:bg-white/5"
    )}
  >
    <Icon size={18} />
    <span className="font-medium text-sm">{children}</span>
  </button>
);

const CodeBlock = ({ language, code }) => {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Code copied to clipboard');
  };

  return (
    <div className="relative group rounded-xl overflow-hidden bg-[#0d1117] border border-white/5">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-white/5">
        <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest">{language}</span>
        <button onClick={copy} className="hover:text-white text-muted-foreground transition-colors">
          {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
        </button>
      </div>
      <pre className="p-4 text-xs font-mono text-blue-100 overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );
};

const Ingestion = () => {
  const [activeTab, setActiveTab] = useState('upload');
  const [file, setFile] = useState(null);
  const [pastedLogs, setPastedLogs] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [subTab, setSubTab] = useState('webhook');
  const [brokerUrl, setBrokerUrl] = useState('localhost:9092');
  const [queueName, setQueueName] = useState('logs-topic');
  const [queueType, setQueueType] = useState('kafka');
  const [otelProp, setOtelProp] = useState(true);
  const [queueConnected, setQueueConnected] = useState(false);

  // (D) Send Test OTel Log Payload
  const handleSendTestOtel = async () => {
    setIsLoading(true);
    try {
      const otlpPayload = {
        resourceLogs: [
          {
            resource: {
              attributes: [{ key: "service.name", value: { stringValue: "order-service-otel" } }]
            },
            scopeLogs: [
              {
                logRecords: [
                  {
                    traceId: "0af7651916cd43dd8448eb211c80319c",
                    spanId: "b5c841381d8d9efd",
                    severityText: "ERROR",
                    body: { stringValue: "081109 203602 ERROR order-service: Failed to process credit card payment block blk_909" }
                  }
                ]
              }
            ]
          }
        ]
      };
      await api.post('/integration/otlp/logs', otlpPayload);
      toast.success('Test OpenTelemetry log payload ingested successfully!');
    } catch (error) {
      toast.error('Failed to ingest OTel payload');
    } finally {
      setIsLoading(false);
    }
  };

  // (E) Connect Queue
  const handleConnectQueue = async () => {
    setIsLoading(true);
    try {
      await api.post('/integration/connect', {
        type: queueType,
        name: queueName,
        broker_url: brokerUrl,
        otel_propagation: otelProp
      });
      setQueueConnected(true);
      toast.success(`Listening to ${queueType} stream on '${queueName}' with trace context propagation`);
    } catch (error) {
      toast.error('Failed to establish connection');
    } finally {
      setIsLoading(false);
    }
  };

  // (A) Upload Logic
  const handleUpload = async () => {
    if (!file) return toast.error('Please select a file');
    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      await api.post('/logs/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success('File uploaded and processed successfully');
      setFile(null);
    } catch (error) {
      toast.error('Upload failed');
    } finally {
      setIsLoading(false);
    }
  };

  // (B) Paste Logic
  const handlePaste = async () => {
    if (!pastedLogs.trim()) return toast.error('Please enter some logs');
    setIsLoading(true);
    try {
      // Split logs by newline and clean
      const logsArray = pastedLogs.split('\n').filter(l => l.trim());
      await api.post('/logs/paste', { logs: logsArray, service: 'manual_upload' });
      toast.success('Logs processed successfully');
      setPastedLogs('');
    } catch (error) {
      toast.error('Processing failed');
    } finally {
      setIsLoading(false);
    }
  };

  // (C) API Key Logic
  const generateApiKey = async () => {
    setIsLoading(true);
    try {
      const { data } = await api.post('/integration/create-api-key');
      setApiKey(data.api_key);
      toast.success('New API key generated');
    } catch (error) {
      toast.error('Failed to generate key');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Log Ingestion</h1>
        <p className="text-muted-foreground">Connect your infrastructure and stream logs to AnomalyAI</p>
      </div>

      <div className="glass rounded-2xl border border-white/5 overflow-hidden">
        <div className="flex border-b border-white/5 bg-card/40 overflow-x-auto scrollbar-hide">
          <TabButton active={activeTab === 'upload'} onClick={() => setActiveTab('upload')} icon={Upload}>Upload File</TabButton>
          <TabButton active={activeTab === 'paste'} onClick={() => setActiveTab('paste')} icon={Terminal}>Paste Logs</TabButton>
          <TabButton active={activeTab === 'api'} onClick={() => setActiveTab('api')} icon={Code}>API Integration</TabButton>
          <TabButton active={activeTab === 'external'} onClick={() => setActiveTab('external')} icon={Share2}>External Services</TabButton>
        </div>

        <div className="p-8">
          <AnimatePresence mode="wait">
            {activeTab === 'upload' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                <div 
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => { e.preventDefault(); setFile(e.dataTransfer.files[0]); }}
                  className="border-2 border-dashed border-border rounded-2xl p-12 text-center transition-all hover:bg-secondary/20 hover:border-primary/50 group cursor-pointer"
                  onClick={() => document.getElementById('file-upload').click()}
                >
                  <input id="file-upload" type="file" className="hidden" accept=".log,.txt" onChange={(e) => setFile(e.target.files[0])} />
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                    <Upload className="text-primary" size={32} />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{file ? file.name : 'Drop your log file here'}</h3>
                  <p className="text-muted-foreground text-sm">Supports .log, .txt files up to 50MB</p>
                </div>
                <button 
                  disabled={!file || isLoading}
                  onClick={handleUpload}
                  className="w-full bg-primary hover:bg-primary/90 text-white py-4 rounded-xl font-semibold shadow-lg shadow-primary/20 disabled:opacity-50"
                >
                  {isLoading ? 'Processing...' : 'Upload & Analyze Logs'}
                </button>
              </motion.div>
            )}

            {activeTab === 'paste' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-4">
                <textarea
                  value={pastedLogs}
                  onChange={(e) => setPastedLogs(e.target.value)}
                  placeholder="Paste your raw logs here. One entry per line..."
                  className="w-full h-80 bg-secondary/30 border border-border rounded-xl p-6 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all resize-none"
                />
                <button 
                  disabled={isLoading || !pastedLogs.trim()}
                  onClick={handlePaste}
                  className="w-full bg-primary hover:bg-primary/90 text-white py-4 rounded-xl font-semibold shadow-lg shadow-primary/20"
                >
                   {isLoading ? 'Analyzing...' : 'Analyze Logs'}
                </button>
              </motion.div>
            )}

            {activeTab === 'api' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-8">
                <div className="p-6 rounded-2xl bg-secondary/30 border border-border flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold mb-1">Microservice API Integration</h3>
                    <p className="text-xs text-muted-foreground">Secure your requests with a unique API key</p>
                  </div>
                  <button 
                    onClick={generateApiKey}
                    className="bg-white text-black px-6 py-2.5 rounded-lg text-sm font-bold hover:bg-white/90 transition-colors"
                  >
                    Generate API Key
                  </button>
                </div>

                {apiKey && (
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
                    <span className="font-mono text-emerald-500 text-sm">{apiKey}</span>
                    <button onClick={() => { navigator.clipboard.writeText(apiKey); toast.success('API Key Copied'); }} className="text-emerald-500 hover:scale-110 transition-transform">
                      <Copy size={18} />
                    </button>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="flex items-center gap-2 text-sm font-semibold opacity-80"><TerminalSquare size={16} /> Python (requests)</h4>
                    <CodeBlock language="python" code={`import requests\n\nurl = "http://localhost:8000/logs/ingest-log"\nheaders = {"X-API-Key": "${apiKey || 'YOUR_KEY_HERE'}"}\ndata = {\n  "service": "web-01",\n  "message": "Internal Server Error",\n  "level": "ERROR"\n}\n\nresponse = requests.post(url, json=data, headers=headers)\nprint(response.json())`} />
                  </div>
                  <div className="space-y-4">
                    <h4 className="flex items-center gap-2 text-sm font-semibold opacity-80"><Code size={16} /> Node.js (axios)</h4>
                    <CodeBlock language="javascript" code={`const axios = require('axios');\n\nconst sendLog = async () => {\n  const res = await axios.post('http://localhost:8000/logs/ingest-log', {\n    service: 'web-01',\n    message: 'Memory threshold exceeded',\n    level: 'CRITICAL'\n  }, {\n    headers: { 'X-API-Key': '${apiKey || 'YOUR_KEY_HERE'}' }\n  });\n  console.log(res.data);\n};`} />
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'external' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-8">
                <div className="flex border-b border-white/5 mb-6">
                  <button 
                    onClick={() => setSubTab('webhook')} 
                    className={cn("px-4 py-2 border-b-2 font-medium text-sm transition-all outline-none", subTab === 'webhook' ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-white")}
                  >
                    OpenTelemetry Webhook
                  </button>
                  <button 
                    onClick={() => setSubTab('queue')} 
                    className={cn("px-4 py-2 border-b-2 font-medium text-sm transition-all outline-none", subTab === 'queue' ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-white")}
                  >
                    Message Queues (Kafka / RabbitMQ)
                  </button>
                </div>

                {subTab === 'webhook' && (
                  <div className="space-y-6">
                    <div className="p-6 rounded-2xl bg-secondary/30 border border-border space-y-4">
                      <div>
                        <h3 className="font-semibold text-lg flex items-center gap-2"><Activity className="text-primary" size={20} /> OpenTelemetry Log Receiver Webhook</h3>
                        <p className="text-sm text-muted-foreground mt-1">Point your OpenTelemetry SDK or OpenTelemetry Collector exporter to this local ingestion pipeline.</p>
                      </div>
                      
                      <div className="space-y-3">
                        <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">OTLP Ingestion Endpoint URL</label>
                        <div className="p-4 rounded-xl bg-[#0d1117] border border-white/5 flex items-center justify-between">
                          <span className="font-mono text-blue-200 text-sm">http://localhost:8000/integration/otlp/logs</span>
                          <button onClick={() => { navigator.clipboard.writeText('http://localhost:8000/integration/otlp/logs'); toast.success('URL Copied'); }} className="text-muted-foreground hover:text-white transition-transform">
                            <Copy size={16} />
                          </button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Collector YAML Snippet</span>
                        <CodeBlock language="yaml" code={`exporters:\n  otlphttp/anomalyai:\n    endpoint: "http://localhost:8000/integration/otlp/logs"\n    headers:\n      X-API-Key: "YOUR_API_KEY"\n\nservice:\n  pipelines:\n    logs:\n      receivers: [otlp]\n      processors: [batch]\n      exporters: [otlphttp/anomalyai]`} />
                      </div>

                      <button 
                        disabled={isLoading}
                        onClick={handleSendTestOtel}
                        className="w-full bg-primary hover:bg-primary/90 text-white py-4 rounded-xl font-semibold shadow-lg shadow-primary/20"
                      >
                        {isLoading ? 'Sending...' : 'Send Test OTLP Log Payload (Order Service)'}
                      </button>
                    </div>
                  </div>
                )}

                {subTab === 'queue' && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-6 rounded-2xl bg-secondary/30 border border-border space-y-4">
                        <h3 className="font-semibold text-lg flex items-center gap-2"><Server className="text-primary" size={20} /> Broker Settings</h3>
                        
                        <div className="space-y-2">
                          <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Queue System</label>
                          <select 
                            value={queueType} 
                            onChange={(e) => setQueueType(e.target.value)}
                            disabled={queueConnected}
                            className="w-full bg-secondary/50 border border-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 ring-primary/20 outline-none text-muted-foreground"
                          >
                            <option value="kafka">Apache Kafka</option>
                            <option value="rabbitmq">RabbitMQ (AMQP)</option>
                          </select>
                        </div>

                        <div className="space-y-2">
                          <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Bootstrap Servers / AMQP URL</label>
                          <input 
                            type="text" 
                            value={brokerUrl} 
                            onChange={(e) => setBrokerUrl(e.target.value)}
                            disabled={queueConnected}
                            placeholder={queueType === 'kafka' ? 'localhost:9092' : 'amqp://guest:guest@localhost:5672/'}
                            className="w-full bg-secondary/50 border border-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 ring-primary/20 outline-none"
                          />
                        </div>

                        <div className="space-y-2">
                          <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Topic / Queue Name</label>
                          <input 
                            type="text" 
                            value={queueName} 
                            onChange={(e) => setQueueName(e.target.value)}
                            disabled={queueConnected}
                            placeholder="log-stream"
                            className="w-full bg-secondary/50 border border-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 ring-primary/20 outline-none"
                          />
                        </div>

                        <div className="flex items-center gap-3 pt-2">
                          <input 
                            type="checkbox" 
                            id="otel-prop" 
                            checked={otelProp} 
                            onChange={(e) => setOtelProp(e.target.checked)}
                            disabled={queueConnected}
                            className="w-4 h-4 rounded border-border text-primary focus:ring-primary/20"
                          />
                          <label htmlFor="otel-prop" className="text-sm font-medium text-muted-foreground select-none cursor-pointer">Enable OTel context propagation</label>
                        </div>

                        {!queueConnected ? (
                          <button 
                            disabled={isLoading}
                            onClick={handleConnectQueue}
                            className="w-full bg-primary hover:bg-primary/90 text-white py-4 rounded-xl font-semibold shadow-lg shadow-primary/20"
                          >
                            {isLoading ? 'Connecting...' : 'Establish Connection & Listen'}
                          </button>
                        ) : (
                          <button 
                            onClick={() => setQueueConnected(false)}
                            className="w-full bg-destructive/10 text-destructive hover:bg-destructive/20 border border-destructive/20 py-4 rounded-xl font-semibold transition-colors"
                          >
                            Disconnect Stream
                          </button>
                        )}
                      </div>

                      <div className="p-6 rounded-2xl bg-secondary/30 border border-border flex flex-col justify-between min-h-[300px]">
                        <div>
                          <h3 className="font-semibold text-lg flex items-center gap-2"><Radio className="text-primary" size={20} /> Connection Status</h3>
                          <p className="text-xs text-muted-foreground mt-1">Real-time state of external event broker ingestion</p>
                        </div>

                        {queueConnected ? (
                          <div className="space-y-4 my-6">
                            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-3">
                              <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                              </span>
                              <div>
                                <p className="text-sm font-bold text-emerald-500">Active Ingestion In Progress</p>
                                <p className="text-xs text-muted-foreground mt-0.5">Listening to {queueType.toUpperCase()} on topic '{queueName}'</p>
                              </div>
                            </div>

                            <div className="p-4 rounded-xl bg-[#0d1117] border border-white/5 space-y-2">
                              <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider flex items-center gap-1.5"><Wifi size={10} /> Simulator Event Stream</p>
                              <div className="text-[11px] font-mono text-emerald-400/90 space-y-1 max-h-32 overflow-y-auto">
                                <div>[OK] Connected to broker {brokerUrl}</div>
                                <div>[STREAM] Subscribed to topic '{queueName}'</div>
                                <div>[STREAM] Awaiting queue packages...</div>
                                <div>[OTEL] Trace propagation handler active</div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="text-center py-12 space-y-3">
                            <Wifi className="text-muted-foreground mx-auto opacity-30 animate-pulse" size={48} />
                            <p className="text-sm font-semibold text-muted-foreground">Queue Connection Inactive</p>
                            <p className="text-xs text-muted-foreground">Configure broker and click Connect to trigger real-time simulated log streaming</p>
                          </div>
                        )}

                        <div className="text-[11px] text-muted-foreground bg-white/5 p-3 rounded-lg border border-white/5">
                          <strong>Note:</strong> Connecting triggers a backend task simulating log events containing randomized OpenTelemetry trace contexts.
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default Ingestion;
