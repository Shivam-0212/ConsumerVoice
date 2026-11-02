import React, { useEffect, useState } from 'react';
import { fetchEvaluations, setActiveModel } from '../services/api';
import {
  Cpu,
  Layers,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  TrendingUp,
  BarChart2,
  ChevronDown,
  ChevronUp,
  Info,
  Check
} from 'lucide-react';

export default function ModelLab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeModel, setModelName] = useState('sentiment_baseline');
  const [switchLoading, setSwitchLoading] = useState(false);
  const [detailedExpanded, setDetailedExpanded] = useState(false);

  const loadData = () => {
    setLoading(true);
    fetchEvaluations()
      .then((res) => {
        setData(res);
        if (res.active_model) setModelName(res.active_model);
        setError(null);
      })
      .catch((err) => {
        console.error('Failed to load evaluation metrics:', err);
        setError('Could not retrieve model evaluation records.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleModelSwitch = async (modelName) => {
    setSwitchLoading(true);
    try {
      await setActiveModel(modelName);
      setModelName(modelName);
      loadData();
    } catch (err) {
      alert(`Cannot switch to ${modelName}. Make sure checkpoint is loaded.`);
    } finally {
      setSwitchLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-brand-500" />
        <p className="text-sm text-slate-400">Loading model performance metrics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-800 text-center max-w-lg mx-auto mt-12">
        <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-rose-200">Unable to load evaluation metrics</h3>
        <p className="text-xs text-rose-300 mt-1">{error}</p>
        <button
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-500 rounded-lg text-xs font-semibold text-white"
        >
          Retry
        </button>
      </div>
    );
  }

  const baseline = data?.evaluations?.sentiment_baseline?.test_metrics;
  const transformer = data?.evaluations?.transformer_distilbert?.test_metrics;

  const baselineCm = baseline?.confusion_matrix?.matrix || [
    [1495, 262, 76],
    [114, 282, 96],
    [256, 590, 6018],
  ];

  const transformerCm = transformer?.confusion_matrix?.matrix || [
    [1603, 147, 83],
    [123, 228, 141],
    [139, 155, 6570],
  ];

  const cmLabels = ['Negative', 'Neutral', 'Positive'];

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Cpu className="w-6 h-6 text-brand-400" />
          <span>Model Performance Comparison</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Compare traditional machine learning with our fine-tuned Transformer model on 9,189 independent test records.
        </p>
      </div>

      {/* Model Cards with Active Model Switcher */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* MODEL A: Logistic Regression */}
        <div
          className={`p-6 rounded-xl border transition-all ${
            activeModel === 'sentiment_baseline'
              ? 'bg-slate-900 border-brand-500/50 shadow-md shadow-brand-500/10'
              : 'bg-slate-900/60 border-slate-800'
          }`}
        >
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">MODEL A &bull; BASELINE</span>
              <h3 className="text-lg font-bold text-white mt-0.5">TF-IDF + Logistic Regression</h3>
              <p className="text-xs text-slate-400 mt-1">40,000 n-gram features with balanced class weights</p>
            </div>
            {activeModel === 'sentiment_baseline' ? (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/40">
                Active Model
              </span>
            ) : (
              <button
                onClick={() => handleModelSwitch('sentiment_baseline')}
                disabled={switchLoading}
                className="px-3 py-1 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
              >
                Set as Active
              </button>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3 mt-5 pt-4 border-t border-slate-800/80 font-mono text-center">
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-sans text-slate-400 block">Accuracy</span>
              <span className="text-base font-bold text-white">84.8%</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-sans text-slate-400 block">Macro F1</span>
              <span className="text-base font-bold text-brand-300">0.692</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-sans text-slate-400 block">Weighted F1</span>
              <span className="text-base font-bold text-slate-200">0.869</span>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 mt-4 space-y-1">
            <div>&bull; Fast CPU inference (~0.01 ms / sample)</div>
            <div>&bull; Supports direct algebraic feature attribution (xᵢ · βₖ)</div>
          </div>
        </div>

        {/* MODEL B: Fine-Tuned DistilBERT */}
        <div
          className={`p-6 rounded-xl border transition-all ${
            activeModel === 'transformer_distilbert'
              ? 'bg-slate-900 border-brand-500/50 shadow-md shadow-brand-500/10'
              : 'bg-slate-900/60 border-slate-800'
          }`}
        >
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 block">MODEL B &bull; TRANSFORMER</span>
              <h3 className="text-lg font-bold text-white mt-0.5">Fine-Tuned DistilBERT</h3>
              <p className="text-xs text-slate-400 mt-1">distilbert-base-uncased fine-tuned on Flipkart reviews</p>
            </div>
            {activeModel === 'transformer_distilbert' ? (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                Active Model
              </span>
            ) : (
              <button
                onClick={() => handleModelSwitch('transformer_distilbert')}
                disabled={switchLoading}
                className="px-3 py-1 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
              >
                Set as Active
              </button>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3 mt-5 pt-4 border-t border-slate-800/80 font-mono text-center">
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-sans text-slate-400 block">Accuracy</span>
              <span className="text-base font-bold text-emerald-400">91.4%</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-sans text-slate-400 block">Macro F1</span>
              <span className="text-base font-bold text-emerald-300">0.758</span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-sans text-slate-400 block">Weighted F1</span>
              <span className="text-base font-bold text-slate-200">0.915</span>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 mt-4 space-y-1">
            <div>&bull; Fine-tuned on Google Colab T4 GPU (3 epochs, lr 2e-5)</div>
            <div>&bull; +6.59% accuracy improvement over baseline on test set</div>
          </div>
        </div>
      </div>

      {/* Main Comparison Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">Independent Test Split Benchmark</h3>
            <p className="text-xs text-slate-400">Evaluated on identical 9,189 held-out Flipkart test samples</p>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-950 text-slate-300 border border-slate-800">
            N = 9,189 samples
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase text-[11px] font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Evaluation Metric</th>
                <th className="py-3 px-4 text-right">Model A (LogReg Baseline)</th>
                <th className="py-3 px-4 text-right">Model B (DistilBERT Fine-Tuned)</th>
                <th className="py-3 px-4 text-right">Delta Improvement</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              <tr className="hover:bg-slate-800/20">
                <td className="py-3 px-4 font-sans font-medium text-slate-200">Overall Accuracy</td>
                <td className="py-3 px-4 text-right text-slate-300">84.83%</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">91.42%</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">+6.59%</td>
              </tr>
              <tr className="hover:bg-slate-800/20">
                <td className="py-3 px-4 font-sans font-medium text-slate-200">Macro F1-Score</td>
                <td className="py-3 px-4 text-right text-slate-300">0.6925</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">0.7584</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">+0.0659</td>
              </tr>
              <tr className="hover:bg-slate-800/20">
                <td className="py-3 px-4 font-sans font-medium text-slate-200">Weighted F1-Score</td>
                <td className="py-3 px-4 text-right text-slate-300">0.8686</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">0.9155</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">+0.0469</td>
              </tr>
              <tr className="hover:bg-slate-800/20">
                <td className="py-3 px-4 font-sans font-medium text-slate-200">Macro Precision</td>
                <td className="py-3 px-4 text-right text-slate-300">0.6742</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">0.7522</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">+0.0780</td>
              </tr>
              <tr className="hover:bg-slate-800/20">
                <td className="py-3 px-4 font-sans font-medium text-slate-200">Macro Recall</td>
                <td className="py-3 px-4 text-right text-slate-300">0.7552</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">0.7650</td>
                <td className="py-3 px-4 text-right text-emerald-400 font-bold">+0.0098</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Class-Wise Performance Comparison */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-white">Class-Wise Performance Breakdown</h3>
          <p className="text-xs text-slate-400">
            Per-class precision, recall, and F1 across Negative, Neutral, and Positive test records
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          {/* Negative */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between font-sans border-b border-slate-800/80 pb-2">
              <span className="font-bold text-rose-400">Negative Class</span>
              <span className="text-[11px] text-slate-400">1,833 samples</span>
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">LogReg F1:</span>
                <span className="text-slate-200">0.8085</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT F1:</span>
                <span className="text-emerald-400 font-bold">0.8670</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT Precision:</span>
                <span className="text-slate-200">0.8595</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT Recall:</span>
                <span className="text-slate-200">0.8745</span>
              </div>
            </div>
          </div>

          {/* Neutral */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between font-sans border-b border-slate-800/80 pb-2">
              <span className="font-bold text-amber-400">Neutral Class</span>
              <span className="text-[11px] text-slate-400">492 samples</span>
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">LogReg F1:</span>
                <span className="text-slate-200">0.3469</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT F1:</span>
                <span className="text-emerald-400 font-bold">0.4462</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT Precision:</span>
                <span className="text-slate-200">0.4302</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT Recall:</span>
                <span className="text-slate-200">0.4634</span>
              </div>
            </div>
          </div>

          {/* Positive */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between font-sans border-b border-slate-800/80 pb-2">
              <span className="font-bold text-emerald-400">Positive Class</span>
              <span className="text-[11px] text-slate-400">6,864 samples</span>
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">LogReg F1:</span>
                <span className="text-slate-200">0.9220</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT F1:</span>
                <span className="text-emerald-400 font-bold">0.9621</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT Precision:</span>
                <span className="text-slate-200">0.9670</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">DistilBERT Recall:</span>
                <span className="text-slate-200">0.9572</span>
              </div>
            </div>
          </div>
        </div>

        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-300">
          <strong>Key Academic Finding:</strong> DistilBERT achieved better overall test performance (+6.59% Macro F1), while Logistic Regression provides lightweight inference and coefficient-based explanations. Neutral sentiment remains the most challenging class across both models due to lower representation and subjective expressions in brief feedback.
        </div>
      </div>

      {/* Expandable Section: View Detailed Evaluation */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <button
          type="button"
          onClick={() => setDetailedExpanded((prev) => !prev)}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-850/60 transition text-left"
        >
          <div className="flex items-center gap-2.5">
            <BarChart2 className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-bold text-white">View Detailed Evaluation (Confusion Matrices & Hardware)</h3>
              <p className="text-xs text-slate-400">
                Inspect 3x3 classification matrices and training environment details
              </p>
            </div>
          </div>
          {detailedExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </button>

        {detailedExpanded && (
          <div className="p-5 border-t border-slate-800 bg-slate-950/40 space-y-6 text-xs">
            {/* Confusion Matrices Side by Side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Baseline Confusion Matrix */}
              <div className="space-y-3">
                <div className="font-semibold text-slate-200 text-xs">
                  Model A Confusion Matrix (Logistic Regression)
                </div>
                <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-3">
                  <table className="w-full text-center font-mono text-xs">
                    <thead>
                      <tr className="text-slate-400 text-[10px] uppercase">
                        <th className="p-1.5 text-left font-sans">True \ Pred</th>
                        <th className="p-1.5">Neg</th>
                        <th className="p-1.5">Neu</th>
                        <th className="p-1.5">Pos</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {baselineCm.map((row, rIdx) => (
                        <tr key={rIdx}>
                          <td className="p-1.5 text-left font-sans text-slate-400 font-semibold">{cmLabels[rIdx]}</td>
                          {row.map((val, cIdx) => (
                            <td
                              key={cIdx}
                              className={`p-1.5 ${
                                rIdx === cIdx ? 'bg-brand-500/15 text-brand-300 font-bold' : 'text-slate-400'
                              }`}
                            >
                              {val.toLocaleString()}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* DistilBERT Confusion Matrix */}
              <div className="space-y-3">
                <div className="font-semibold text-slate-200 text-xs">
                  Model B Confusion Matrix (Fine-Tuned DistilBERT)
                </div>
                <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-3">
                  <table className="w-full text-center font-mono text-xs">
                    <thead>
                      <tr className="text-slate-400 text-[10px] uppercase">
                        <th className="p-1.5 text-left font-sans">True \ Pred</th>
                        <th className="p-1.5">Neg</th>
                        <th className="p-1.5">Neu</th>
                        <th className="p-1.5">Pos</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {transformerCm.map((row, rIdx) => (
                        <tr key={rIdx}>
                          <td className="p-1.5 text-left font-sans text-slate-400 font-semibold">{cmLabels[rIdx]}</td>
                          {row.map((val, cIdx) => (
                            <td
                              key={cIdx}
                              className={`p-1.5 ${
                                rIdx === cIdx ? 'bg-emerald-500/15 text-emerald-300 font-bold' : 'text-slate-400'
                              }`}
                            >
                              {val.toLocaleString()}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Hardware & Training Parameters Comparison */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <span className="font-semibold text-white text-xs block">Training Environment & Hardware Context</span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-300 text-xs">
                <div className="space-y-1">
                  <strong className="text-slate-200">Logistic Regression Baseline:</strong>
                  <p className="text-slate-400 text-[11px]">
                    Trained locally on CPU (Apple M2) in 2.48 seconds using Scikit-learn Pipeline with 40,000 sublinear TF-IDF features.
                  </p>
                </div>
                <div className="space-y-1">
                  <strong className="text-slate-200">Fine-Tuned DistilBERT:</strong>
                  <p className="text-slate-400 text-[11px]">
                    Fine-tuned on Google Colab with an NVIDIA T4 GPU (16GB VRAM) for 3 epochs (891.31s total), sequence length 192, and weight decay 0.01. Safe CPU inference is verified for local deployment.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
