import React, { useEffect, useState } from 'react';
import { fetchHealth } from '../services/api';
import { RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Navbar() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkHealth = () => {
    fetchHealth()
      .then((data) => setHealth(data))
      .catch((err) => console.error('Health check failed:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-30 px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
          Customer Feedback Intelligence Platform
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* System Health Indicator */}
        <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60">
          {loading ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-400" />
          ) : health?.status === 'healthy' ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-slate-300 font-medium">System Operational</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-rose-400 font-medium">Offline</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
