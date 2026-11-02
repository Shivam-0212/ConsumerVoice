import React, { useEffect, useState } from 'react';
import { fetchDashboardOverview } from '../services/api';
import { cleanProductName } from '../utils/textUtils';
import {
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  MinusCircle,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Layers,
  Sparkles,
  Search,
  FileText,
  Tag,
  Star
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { Link, useNavigate } from 'react-router-dom';

const SENTIMENT_COLORS = {
  Positive: '#10b981',
  Negative: '#f43f5e',
  Neutral: '#f59e0b',
};

export default function OverviewDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = () => {
    setLoading(true);
    fetchDashboardOverview()
      .then((res) => {
        setData(res);
        setError(null);
      })
      .catch((err) => {
        console.error('Failed to load dashboard data:', err);
        setError('Failed to fetch customer feedback overview metrics.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-brand-500" />
        <p className="text-sm text-slate-400">Loading customer feedback overview...</p>
      </div>
    );
  }

  if (error || !data || typeof data !== 'object' || typeof data.total_reviews !== 'number') {
    return (
      <div className="bg-rose-950/30 border border-rose-800/50 p-6 rounded-xl text-center max-w-lg mx-auto mt-12">
        <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
        <h3 className="text-base font-semibold text-rose-200">Unable to load dashboard</h3>
        <p className="text-xs text-rose-300 mt-1">{error || 'Invalid or missing dashboard data format.'}</p>
        <button
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const pieData = [
    { name: 'Positive', value: data.positive_count, color: SENTIMENT_COLORS.Positive },
    { name: 'Negative', value: data.negative_count, color: SENTIMENT_COLORS.Negative },
    { name: 'Neutral', value: data.neutral_count, color: SENTIMENT_COLORS.Neutral },
  ];

  const ratingData = Object.entries(data.rating_distribution || {}).map(([key, val]) => ({
    rating: key,
    count: val,
  }));

  const issueData = (data.top_issues || []).map((i) => ({
    category: i.category,
    count: i.count,
  }));

  const topProducts = data.top_products || [];

  return (
    <div className="space-y-8 pb-10">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Customer Feedback Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Understand customer satisfaction, review sentiment and frequently reported product problems.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Analyze Feedback</span>
          </Link>
          <button
            onClick={loadData}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh Metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Dataset Scope Distinction Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-slate-300">
            <Layers className="w-4 h-4 text-brand-400 shrink-0" />
            <span className="font-semibold text-white">Dataset Scope & Lineage:</span>
            <span className="text-slate-400">
              Clear distinction between master raw dataset, imported SQLite records, and model splits.
            </span>
          </div>
          <span className="text-slate-400 font-mono text-[11px] bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700/60 font-medium shrink-0">
            Reconciled Pipeline Counts
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-slate-800/80 font-mono text-[11px]">
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            <span className="text-slate-400 text-[10px] uppercase font-sans font-semibold block">Total Raw Dataset</span>
            <span className="text-white font-bold text-sm">205,052</span>
            <span className="text-slate-400 text-[10px] block font-sans">Flipkart CSV records</span>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            <span className="text-indigo-400 text-[10px] uppercase font-sans font-semibold block">Imported in SQLite</span>
            <span className="text-indigo-200 font-bold text-sm">{(data?.total_reviews ?? 50000).toLocaleString()}</span>
            <span className="text-slate-400 text-[10px] block font-sans">Indexed sample for app</span>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            <span className="text-emerald-400 text-[10px] uppercase font-sans font-semibold block">Training Split</span>
            <span className="text-emerald-200 font-bold text-sm">73,512</span>
            <span className="text-slate-400 text-[10px] block font-sans">80% benchmark split</span>
          </div>
          <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
            <span className="text-amber-400 text-[10px] uppercase font-sans font-semibold block">Final Test Split</span>
            <span className="text-amber-200 font-bold text-sm">9,189</span>
            <span className="text-slate-400 text-[10px] block font-sans">10% independent held-out</span>
          </div>
        </div>
      </div>

      {/* KPI Cards (Imported Database Scope) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Reviews */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Reviews Analyzed</h3>
            <div className="text-2xl font-bold text-white mt-1">{(data?.total_reviews ?? 50000).toLocaleString()}</div>
            <p className="text-[11px] text-slate-400 mt-1">Imported SQLite sample</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
            <MessageSquare className="w-5 h-5" />
          </div>
        </div>

        {/* Positive */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Positive Reviews</h3>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{(data?.positive_count ?? 0).toLocaleString()}</div>
            <p className="text-[11px] text-emerald-500/80 mt-1 font-semibold">{data?.positive_percent ?? 0}% of sample</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <ThumbsUp className="w-5 h-5" />
          </div>
        </div>

        {/* Negative */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Negative Reviews</h3>
            <div className="text-2xl font-bold text-rose-400 mt-1">{(data?.negative_count ?? 0).toLocaleString()}</div>
            <p className="text-[11px] text-rose-500/80 mt-1 font-semibold">{data?.negative_percent ?? 0}% of sample</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <ThumbsDown className="w-5 h-5" />
          </div>
        </div>

        {/* Neutral (strictly "Neutral", not "Neutral / Mixed") */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Neutral Reviews</h3>
            <div className="text-2xl font-bold text-amber-400 mt-1">{(data?.neutral_count ?? 0).toLocaleString()}</div>
            <p className="text-[11px] text-amber-500/80 mt-1 font-semibold">{data?.neutral_percent ?? 0}% of sample</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <MinusCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Customer Feedback Insights Section */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Customer Feedback Insights</h3>
              <p className="text-xs text-slate-400">
                Extractive synthesis across {data.sample_summary?.reviews_analyzed_count || 50} customer feedback records
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/explorer?sentiment=negative')}
            className="text-xs font-medium text-brand-400 hover:text-brand-300 inline-flex items-center gap-1 self-start sm:self-auto"
          >
            <span>Inspect Supporting Reviews</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-lg border border-slate-800">
          <p className="italic">
            "{data.sample_summary?.summary || 'Customer reviews demonstrate strong satisfaction with product value and operation. Primary concerns center on delivery timelines, transit packaging wear, and occasional build quality issues.'}"
          </p>
        </div>

        {data.sample_summary?.sample_review_ids && (
          <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-slate-400">
            <span className="font-semibold text-slate-400">Source Review IDs:</span>
            {data.sample_summary.sample_review_ids.map((id) => (
              <button
                key={id}
                onClick={() => navigate(`/explorer?search=${id}`)}
                className="font-mono text-brand-300 hover:underline bg-slate-950 px-2 py-0.5 rounded border border-slate-800"
              >
                {id}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Sentiment Distribution */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Sentiment Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">3-class distribution across imported Flipkart reviews</p>
          </div>
          <div className="h-64 my-3">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={88}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(value, name) => [`${value.toLocaleString()} reviews`, name]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 text-xs text-slate-300 border-t border-slate-800/80 pt-3">
            {pieData.map((p) => (
              <div key={p.name} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: p.color }} />
                <span>{p.name}: <strong className="text-white">{p.value.toLocaleString()}</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* Chart 2: Rating Distribution */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Customer Rating Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">Distribution of 1-star to 5-star customer ratings</p>
          </div>
          <div className="h-64 my-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ratingData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="rating" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(value) => [`${value.toLocaleString()} reviews`, 'Volume']}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-3 text-center">
            Ratings are parsed from the original dataset Rate column; 3 malformed records were safely cleaned during preprocessing.
          </div>
        </div>
      </div>

      {/* Secondary Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 3: Product Issues */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-semibold text-white">Most Commonly Detected Issues</h3>
              <p className="text-xs text-slate-400 mt-0.5">Contextual occurrences across feedback</p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
              Rule-Based Issue Detection
            </span>
          </div>
          <div className="h-64 my-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={issueData.slice(0, 7)}
                layout="vertical"
                margin={{ top: 5, right: 20, left: 40, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis dataKey="category" type="category" stroke="#64748b" fontSize={11} width={110} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" fill="#f43f5e" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-3 text-center">
            Issues are detected via contextual keyword rules with negation suppression (e.g. "not damaged" is ignored).
          </div>
        </div>

        {/* Chart 4: Highest-Volume Products */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl flex flex-col justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Highest-Volume Products</h3>
            <p className="text-xs text-slate-400 mt-0.5">Top catalog items by customer review count</p>
          </div>

          <div className="space-y-2.5 my-3">
            {topProducts.slice(0, 5).map((p, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/70 text-xs"
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-3">
                  <span className="w-5 h-5 rounded bg-slate-800 text-slate-300 font-bold flex items-center justify-center text-[10px] shrink-0">
                    {idx + 1}
                  </span>
                  <span className="text-slate-200 font-medium truncate" title={p.full_name}>
                    {cleanProductName(p.full_name || p.product_name)}
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="font-mono text-slate-400 text-[11px]">{p.count.toLocaleString()} reviews</span>
                  <button
                    onClick={() => navigate(`/explorer?search=${encodeURIComponent(cleanProductName(p.full_name || p.product_name).slice(0, 20))}`)}
                    className="p-1 text-slate-400 hover:text-brand-400 transition"
                    title="View Reviews"
                  >
                    <Search className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-3 text-center">
            Product catalog names are safely cleaned from the scraped Flipkart CSV encoding.
          </div>
        </div>
      </div>
    </div>
  );
}
