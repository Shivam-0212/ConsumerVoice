import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchReviews, fetchReviewDetail, generateSummary, analyzeReview } from '../services/api';
import { cleanProductName, formatRating } from '../utils/textUtils';
import {
  Search,
  Filter,
  Star,
  Eye,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  X,
  FileText,
  Sparkles,
  Bot,
  AlertCircle,
  Tag,
  ArrowRight,
  CheckCircle2,
  Copy,
  Check
} from 'lucide-react';

export default function ReviewExplorer() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [reviews, setReviews] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
  const [sentimentFilter, setSentimentFilter] = useState(searchParams.get('sentiment') || '');
  const [rateFilter, setRateFilter] = useState(searchParams.get('rate') || '');

  // Detail Modal
  const [selectedReviewId, setSelectedReviewId] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [livePrediction, setLivePrediction] = useState(null);
  const [livePredictionLoading, setLivePredictionLoading] = useState(false);

  // Summarize Filtered Reviews Modal
  const [summaryModalOpen, setSummaryModalOpen] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryResult, setSummaryResult] = useState(null);
  const [summaryError, setSummaryError] = useState(null);
  const [copiedSummary, setCopiedSummary] = useState(false);

  const loadReviews = (p = page) => {
    setLoading(true);
    const params = {
      page: p,
      page_size: pageSize,
    };
    if (searchTerm.trim()) params.search = searchTerm.trim();
    if (sentimentFilter) params.sentiment = sentimentFilter;
    if (rateFilter) params.rate = parseFloat(rateFilter);

    fetchReviews(params)
      .then((res) => {
        setReviews(res.items);
        setTotal(res.total);
        setPage(res.page);
        setTotalPages(res.total_pages);
      })
      .catch((err) => console.error('Failed to load reviews:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const newParams = {};
    if (searchTerm.trim()) newParams.search = searchTerm.trim();
    if (sentimentFilter) newParams.sentiment = sentimentFilter;
    if (rateFilter) newParams.rate = rateFilter;
    setSearchParams(newParams);
    loadReviews(1);
  }, [sentimentFilter, rateFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const newParams = {};
    if (searchTerm.trim()) newParams.search = searchTerm.trim();
    if (sentimentFilter) newParams.sentiment = sentimentFilter;
    if (rateFilter) newParams.rate = rateFilter;
    setSearchParams(newParams);
    loadReviews(1);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSentimentFilter('');
    setRateFilter('');
    setSearchParams({});
    loadReviews(1);
  };

  const openDetail = (id) => {
    setSelectedReviewId(id);
    setDetailLoading(true);
    setLivePrediction(null);
    fetchReviewDetail(id)
      .then((data) => setDetailData(data))
      .catch((err) => console.error('Detail fetch error:', err))
      .finally(() => setDetailLoading(false));
  };

  const closeDetail = () => {
    setSelectedReviewId(null);
    setDetailData(null);
    setLivePrediction(null);
  };

  const handleRunLivePrediction = async (text) => {
    if (!text) return;
    setLivePredictionLoading(true);
    try {
      const pred = await analyzeReview({ text, include_explanation: false });
      setLivePrediction(pred);
    } catch (err) {
      console.error('Live prediction error:', err);
    } finally {
      setLivePredictionLoading(false);
    }
  };

  const handleSummarizeFiltered = async () => {
    setSummaryModalOpen(true);
    setSummaryLoading(true);
    setSummaryError(null);
    setSummaryResult(null);

    try {
      // Gather active review IDs from current filtered set or pass active filter params
      const payload = {
        prefer_abstractive: false,
        sample_size: Math.min(reviews.length > 0 ? reviews.length : 25, 50),
      };

      if (reviews.length > 0) {
        payload.review_ids = reviews.map((r) => r.review_id);
      }
      if (sentimentFilter) payload.sentiment = sentimentFilter;

      const result = await generateSummary(payload);
      setSummaryResult(result);
    } catch (err) {
      console.error('Summarization failed:', err);
      setSummaryError('Could not summarize the selected reviews. Please try with broader filters.');
    } finally {
      setSummaryLoading(false);
    }
  };

  const getSentimentBadge = (sentiment) => {
    const s = (sentiment || '').toLowerCase();
    if (s === 'positive') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Positive
        </span>
      );
    }
    if (s === 'negative') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          Negative
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
        Neutral
      </span>
    );
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Explore Customer Reviews</h1>
          <p className="text-sm text-slate-400 mt-1">
            Search and inspect real Flipkart customer reviews, ratings, and dataset ground truth.
          </p>
        </div>

        {/* Summarize Filtered Reviews Action */}
        <button
          onClick={handleSummarizeFiltered}
          disabled={loading || reviews.length === 0}
          className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition shadow-sm shrink-0 self-start sm:self-auto"
        >
          <FileText className="w-4 h-4" />
          <span>Summarize Filtered Reviews</span>
        </button>
      </div>

      {/* Search and Filters Bar */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by summary, review text, or product name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition shrink-0"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Sentiment Filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <select
              value={sentimentFilter}
              onChange={(e) => setSentimentFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Sentiments</option>
              <option value="positive">Positive</option>
              <option value="negative">Negative</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>

          {/* Rating Filter */}
          <div>
            <select
              value={rateFilter}
              onChange={(e) => setRateFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Ratings</option>
              <option value="5">5 Stars</option>
              <option value="4">4 Stars</option>
              <option value="3">3 Stars</option>
              <option value="2">2 Stars</option>
              <option value="1">1 Star</option>
            </select>
          </div>

          {/* Clear Filters */}
          {(searchTerm || sentimentFilter || rateFilter) && (
            <button
              onClick={handleClearFilters}
              className="px-2.5 py-2 bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded-lg text-xs font-medium transition"
            >
              Clear Filters
            </button>
          )}

          <button
            onClick={() => loadReviews(page)}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refresh Table"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Review Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider bg-slate-950/40">
                <th className="py-3.5 px-4 w-28">Record ID</th>
                <th className="py-3.5 px-4 w-52">Product</th>
                <th className="py-3.5 px-4 w-24">Rating</th>
                <th className="py-3.5 px-4">Customer Review / Summary</th>
                <th className="py-3.5 px-4 w-28">Dataset Sentiment</th>
                <th className="py-3.5 px-4 w-24 text-center">View Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin text-brand-500 mx-auto mb-2" />
                    Loading reviews...
                  </td>
                </tr>
              ) : reviews.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No customer reviews found matching your filter criteria.
                  </td>
                </tr>
              ) : (
                reviews.map((r) => (
                  <tr key={r.review_id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono font-medium text-slate-300">{r.review_id}</td>
                    <td className="py-3 px-4 text-slate-300 max-w-xs truncate" title={r.product_name}>
                      {cleanProductName(r.product_name)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="inline-flex items-center gap-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded text-[11px] font-semibold">
                        <Star className="w-3 h-3 fill-amber-400" />
                        <span>{formatRating(r.cleaned_rate || r.rate)}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-200 max-w-md">
                      <div className="font-medium text-white">{r.summary}</div>
                      {r.review_text && (
                        <div className="text-slate-400 text-[11px] truncate mt-0.5">{r.review_text}</div>
                      )}
                    </td>
                    <td className="py-3 px-4">{getSentimentBadge(r.normalized_sentiment)}</td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => openDetail(r.review_id)}
                        className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white transition inline-flex items-center gap-1 text-[11px] font-medium"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400 bg-slate-950/30">
          <div>
            Showing <strong className="text-slate-200">{reviews.length}</strong> of{' '}
            <strong className="text-slate-200">{total.toLocaleString()}</strong> reviews
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadReviews(page - 1)}
              disabled={page <= 1}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-40 transition"
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-slate-300">
              Page {page} of {totalPages || 1}
            </span>
            <button
              onClick={() => loadReviews(page + 1)}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-40 transition"
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* MODAL: Record Detail & Distinction */}
      {selectedReviewId && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
                  {selectedReviewId}
                </span>
                <h3 className="text-lg font-bold text-white mt-1">Review Inspection & Lineage</h3>
              </div>
              <button onClick={closeDetail} className="text-slate-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {detailLoading ? (
              <div className="py-12 text-center text-slate-400">
                <RefreshCw className="w-6 h-6 animate-spin text-brand-500 mx-auto mb-2" />
                Loading review details...
              </div>
            ) : detailData?.review ? (
              <div className="space-y-4 text-xs">
                {/* Product Metadata */}
                <div className="grid grid-cols-2 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Product Name</span>
                    <span className="text-white font-medium block mt-0.5" title={detailData.review.product_name}>
                      {cleanProductName(detailData.review.product_name)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Catalog Price</span>
                    <span className="text-emerald-400 font-mono font-medium block mt-0.5">
                      {detailData.review.product_price ? `₹${detailData.review.product_price}` : 'Not Specified'}
                    </span>
                  </div>
                </div>

                {/* Text Content */}
                <div className="space-y-3">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold mb-1">
                      Original Summary (Primary Classification Input)
                    </span>
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-100 font-medium">
                      "{detailData.review.summary}"
                    </div>
                  </div>

                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold mb-1">
                      Extended Customer Review
                    </span>
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-300">
                      {detailData.review.review_text ? (
                        `"${detailData.review.review_text}"`
                      ) : (
                        <span className="text-slate-400 italic">No extended review text provided (missing in raw dataset).</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Distinction: Dataset Label vs Rating vs ConsumerVoice Live Prediction */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="text-slate-300 font-semibold text-xs border-b border-slate-800/80 pb-2">
                    Distinction: Dataset Ground Truth vs Rating vs Live Model
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                      <span className="text-slate-400 block text-[10px] uppercase">Dataset Sentiment Label</span>
                      <div className="mt-1 flex items-center gap-2">
                        {getSentimentBadge(detailData.review.normalized_sentiment)}
                        <span className="text-[10px] text-slate-400">(from Summary via VADER)</span>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                      <span className="text-slate-400 block text-[10px] uppercase">Customer Rating</span>
                      <div className="mt-1 flex items-center gap-1.5 text-amber-400 font-semibold">
                        <Star className="w-3.5 h-3.5 fill-amber-400" />
                        <span>{formatRating(detailData.review.cleaned_rate || detailData.review.rate)} / 5.0</span>
                      </div>
                    </div>
                  </div>

                  {/* Live Model Prediction */}
                  <div className="p-3 rounded-lg bg-brand-950/30 border border-brand-500/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-brand-300 font-medium">ConsumerVoice Active Model Prediction:</span>
                      <button
                        onClick={() => handleRunLivePrediction(detailData.review.summary)}
                        disabled={livePredictionLoading}
                        className="px-2.5 py-1 bg-brand-600 hover:bg-brand-500 text-white rounded text-[11px] font-medium transition"
                      >
                        {livePredictionLoading ? 'Predicting...' : 'Run Live Prediction'}
                      </button>
                    </div>

                    {livePrediction && (
                      <div className="pt-2 border-t border-brand-500/20 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400">Prediction:</span>
                          {getSentimentBadge(livePrediction.sentiment)}
                        </div>
                        <div className="text-slate-300 font-mono">
                          Confidence: {(livePrediction.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-rose-300">Could not retrieve review data.</p>
            )}

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={closeDetail}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Summarize Filtered Reviews */}
      {summaryModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-brand-400" />
                <div>
                  <h3 className="text-lg font-bold text-white">Summary of Filtered Reviews</h3>
                  <p className="text-xs text-slate-400">
                    Grounded extractive feedback synthesis with source review citations
                  </p>
                </div>
              </div>
              <button onClick={() => setSummaryModalOpen(false)} className="text-slate-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {summaryLoading ? (
              <div className="py-12 text-center text-slate-400">
                <RefreshCw className="w-6 h-6 animate-spin text-brand-500 mx-auto mb-2" />
                Analyzing and summarizing filtered reviews...
              </div>
            ) : summaryError ? (
              <div className="p-4 bg-rose-950/30 border border-rose-800 rounded-xl text-center space-y-2 text-xs">
                <AlertCircle className="w-6 h-6 text-rose-400 mx-auto" />
                <p className="text-rose-200">{summaryError}</p>
              </div>
            ) : summaryResult ? (
              <div className="space-y-4 text-xs">
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800 text-slate-400">
                  <span>
                    Analyzed <strong className="text-white">{summaryResult.total_reviews_analyzed}</strong> filtered reviews
                  </span>
                  <span className="font-mono text-[11px] text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded border border-brand-500/20">
                    Mode: {summaryResult.mode}
                  </span>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-slate-400 font-semibold uppercase text-[10px]">Extractive Summary</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(summaryResult.summary);
                        setCopiedSummary(true);
                        setTimeout(() => setCopiedSummary(false), 2000);
                      }}
                      className="text-brand-400 hover:text-brand-300 inline-flex items-center gap-1 text-[11px]"
                    >
                      {copiedSummary ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedSummary ? 'Copied' : 'Copy Summary'}</span>
                    </button>
                  </div>
                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-slate-200 leading-relaxed text-sm">
                    {summaryResult.summary}
                  </div>
                </div>

                {/* Extracted Supporting Sentences & Citations */}
                {summaryResult.sentence_citations && summaryResult.sentence_citations.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-slate-400 font-semibold uppercase text-[10px]">
                      Extracted Supporting Sentences & Citations
                    </span>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                      {summaryResult.sentence_citations.map((cite, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start justify-between gap-3"
                        >
                          <span className="text-slate-300 italic">"{cite.sentence}"</span>
                          <span className="font-mono text-[10px] text-brand-300 bg-brand-500/10 px-1.5 py-0.5 rounded shrink-0 border border-brand-500/20">
                            {cite.review_id}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}

            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                onClick={() => setSummaryModalOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold"
              >
                Close Summary
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
