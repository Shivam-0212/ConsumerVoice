import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { fetchHealth } from '../services/api';
import {
  LayoutDashboard,
  Search,
  Sparkles,
  Cpu,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  Database
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Review Explorer', path: '/explorer', icon: Search },
  { name: 'Analyze Feedback', path: '/analyze', icon: Sparkles },
  { name: 'Model Comparison', path: '/models', icon: Cpu },
];

export default function Sidebar() {
  const [activeModel, setActiveModel] = useState('sentiment_baseline');
  const [isHealthy, setIsHealthy] = useState(true);

  const checkStatus = () => {
    fetchHealth()
      .then((data) => {
        if (data?.active_model) setActiveModel(data.active_model);
        setIsHealthy(data?.status === 'healthy');
      })
      .catch(() => {
        setIsHealthy(false);
      });
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
          <MessageSquare className="w-5 h-5" />
        </div>
        <div>
          <div className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
            Consumer<span className="text-brand-400">Voice</span>
          </div>
          <p className="text-xs text-slate-400">Customer Feedback NLP</p>
        </div>
      </div>

      {/* Main Navigation (Strictly 4 items) */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Customer Feedback Analysis
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-600/15 text-brand-300 border border-brand-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </div>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-400 flex flex-col gap-2 bg-slate-950/40">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Active Model:</span>
          <span className="text-brand-300 font-mono text-[11px] bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20 font-medium">
            {activeModel === 'transformer_distilbert' ? 'DistilBERT' : 'Logistic Regression'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Dataset:</span>
          <span className="text-slate-300 font-medium text-[11px]">Flipkart Reviews</span>
        </div>
        <div className="flex items-center justify-between pt-1 border-t border-slate-800/60">
          <span className="text-slate-400">Backend Health:</span>
          <span className="flex items-center gap-1.5 text-[11px]">
            {isHealthy ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-emerald-400 font-medium">Operational</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                <span className="text-rose-400 font-medium">Unavailable</span>
              </>
            )}
          </span>
        </div>
      </div>
    </aside>
  );
}
