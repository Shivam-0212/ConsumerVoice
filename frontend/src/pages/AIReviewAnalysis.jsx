import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  analyzeReview,
  generateResponse,
  verifyResponse,
  fetchHealth,
  setActiveModel
} from '../services/api';
import {
  Sparkles,
  Zap,
  CheckCircle2,
  AlertTriangle,
  MinusCircle,
  ThumbsUp,
  ThumbsDown,
  Info,
  RefreshCw,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Bot,
  Layers,
  HelpCircle
} from 'lucide-react';

const PRESETS = [
  {
    type: 'Positive',
    label: 'Positive Review',
    text: 'The product quality is excellent. It works perfectly and I am very satisfied.',
  },
  {
    type: 'Negative',
    label: 'Negative Review',
    text: 'The product arrived damaged. Delivery was late and customer support was unhelpful.',
  },
  {
    type: 'Mixed',
    label: 'Mixed Review',
    text: 'The product quality is good, but delivery was delayed and the packaging was damaged.',
  },
];

export default function AIReviewAnalysis() {
  const location = useLocation();

  const [inputText, setInputText] = useState(
    location.state?.prefill || 'The product quality is good, but delivery was delayed and the packaging was damaged.'
  );
  const [activeModel, setModelName] = useState('sentiment_baseline');
  const [modelSwitching, setModelSwitching] = useState(false);

  // Analysis State
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Optional: Customer Response Assistant
  const [responseExpanded, setResponseExpanded] = useState(false);
  const [responseGenerating, setResponseGenerating] = useState(false);
  const [generatedResponseText, setGeneratedResponseText] = useState('');
  const [responseMeta, setResponseMeta] = useState(null);
  const [copiedResponse, setCopiedResponse] = useState(false);

  // Optional: Response Evidence Screening
  const [safetyExpanded, setSafetyExpanded] = useState(false);
  const [screeningLoading, setScreeningLoading] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  // Load active model on mount, then run initial analysis with that model
  useEffect(() => {
    fetchHealth()
      .then((data) => {
        const currentModel = data?.active_model || 'sentiment_baseline';
        setModelName(currentModel);
        runAnalysis(inputText, currentModel);
      })
      .catch(() => {
        runAnalysis(inputText, 'sentiment_baseline');
      });
  }, []);

  const handleModelChange = async (newModel) => {
    if (newModel === activeModel) return;
    setModelSwitching(true);
    try {
      await setActiveModel(newModel);
      setModelName(newModel);
      // Re-run analysis if there is active text
      if (inputText.trim()) {
        runAnalysis(inputText, newModel);
      }
    } catch (err) {
      console.error('Failed to change active model:', err);
      alert('Could not switch model. Please ensure backend services are running.');
    } finally {
      setModelSwitching(false);
    }
  };

  const runAnalysis = async (textToAnalyze = inputText, modelOverride = activeModel) => {
    if (!textToAnalyze.trim()) {
      setError('Please enter customer feedback text before analyzing.');
      setResult(null);
      return;
    }
    setAnalyzing(true);
    setError(null);
    setVerificationResult(null);

    try {
      const data = await analyzeReview({
        text: textToAnalyze.trim(),
        model_name: modelOverride,
        include_explanation: true,
        save_to_history: true,
      });
      setResult(data);
      if (data.active_model) {
        setModelName(data.active_model);
      }
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Analysis failed. Please verify that the backend is running.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerateResponse = async () => {
    if (!inputText.trim()) return;
    setResponseGenerating(true);
    try {
      const res = await generateResponse({
        customer_text: inputText.trim(),
        sentiment: result?.sentiment,
        detected_issues: result?.issues,
        prefer_template: true,
      });
      setGeneratedResponseText(res.response);
      setResponseMeta(res);
      setVerificationResult(null);
    } catch (err) {
      console.error('Response generation failed:', err);
      alert('Could not generate response. Please try again.');
    } finally {
      setResponseGenerating(false);
    }
  };

  const handleRunSafetyCheck = async () => {
    if (!generatedResponseText.trim() || !inputText.trim()) return;
    setScreeningLoading(true);
    try {
      const ver = await verifyResponse({
        customer_review: inputText.trim(),
        response_text: generatedResponseText.trim(),
      });
      setVerificationResult(ver);
    } catch (err) {
      console.error('Evidence check failed:', err);
      alert('Could not perform evidence check. Please try again.');
    } finally {
      setScreeningLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Sparkles className="w-6 h-6 text-brand-400" />
          <span>Analyze Customer Feedback</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Enter customer feedback to understand sentiment, identify problems and generate useful insights.
        </p>
      </div>

      {/* Main Analysis Input Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
        {/* Model Selection Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3.5">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">Classification Model:</span>
            <div className="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800">
              <button
                type="button"
                onClick={() => handleModelChange('sentiment_baseline')}
                disabled={modelSwitching}
                className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                  activeModel === 'sentiment_baseline'
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Logistic Regression (Baseline)
              </button>
              <button
                type="button"
                onClick={() => handleModelChange('transformer_distilbert')}
                disabled={modelSwitching}
                className={`px-3 py-1 rounded-md text-xs font-medium transition ${
                  activeModel === 'transformer_distilbert'
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Fine-Tuned DistilBERT
              </button>
            </div>
          </div>

          <span className="text-[11px] text-slate-400 flex items-center gap-1.5 self-start sm:self-auto font-mono">
            Active: <strong className="text-brand-300">{activeModel === 'transformer_distilbert' ? 'DistilBERT' : 'Logistic Regression'}</strong>
          </span>
        </div>

        {/* Example Review Presets */}
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 font-semibold flex items-center gap-1 text-[11px]">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              Example Presets:
            </span>
            {PRESETS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setInputText(preset.text);
                  runAnalysis(preset.text, activeModel);
                }}
                className="px-2.5 py-1 rounded-md bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition text-xs"
              >
                {preset.label}
              </button>
            ))}
          </div>
          <p className="text-[11px] text-slate-400 italic">
            Note: The three-class sentiment model will classify mixed reviews into one of the available classes (Positive, Negative, or Neutral).
          </p>
        </div>

        {/* Input Textarea */}
        <div className="relative">
          <textarea
            rows={4}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Enter customer feedback here..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition leading-relaxed resize-y"
          />
        </div>

        {/* Analyze Button */}
        <div className="flex items-center justify-between pt-1">
          <span className="text-[11px] text-slate-400">
            {inputText.trim().split(/\s+/).filter(Boolean).length} words
          </span>
          <button
            type="button"
            onClick={() => runAnalysis()}
            disabled={analyzing || !inputText.trim()}
            className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition shadow-sm flex items-center gap-2"
          >
            {analyzing ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Analyzing Feedback...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Analyze Feedback</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800 rounded-xl text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Sentiment & Probability Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Predicted Sentiment */}
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Predicted Sentiment</span>
                <div className="text-2xl font-bold mt-1 capitalize flex items-center gap-2">
                  {result.sentiment === 'positive' && (
                    <>
                      <ThumbsUp className="w-6 h-6 text-emerald-400" />
                      <span className="text-emerald-400">Positive</span>
                    </>
                  )}
                  {result.sentiment === 'negative' && (
                    <>
                      <ThumbsDown className="w-6 h-6 text-rose-400" />
                      <span className="text-rose-400">Negative</span>
                    </>
                  )}
                  {result.sentiment === 'neutral' && (
                    <>
                      <MinusCircle className="w-6 h-6 text-amber-400" />
                      <span className="text-amber-400">Neutral</span>
                    </>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 mt-1 font-mono">
                  Confidence: <strong className="text-white">{(result.confidence * 100).toFixed(1)}%</strong>
                </div>
              </div>

              <div className="w-12 h-12 rounded-xl bg-slate-950 flex items-center justify-center border border-slate-800 font-mono text-xs text-slate-300">
                {result.active_model === 'transformer_distilbert' ? 'BERT' : 'LR'}
              </div>
            </div>

            {/* Class Probabilities Progress Meters */}
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl md:col-span-2 space-y-3">
              <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider block">
                Class Probabilities ({result.active_model === 'transformer_distilbert' ? 'DistilBERT Softmax' : 'Logistic Regression Softmax'})
              </span>

              <div className="space-y-2 text-xs">
                {/* Positive */}
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-emerald-400 font-medium">Positive</span>
                    <span className="font-mono text-slate-300">
                      {((result.probabilities?.positive || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${(result.probabilities?.positive || 0) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Negative */}
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-rose-400 font-medium">Negative</span>
                    <span className="font-mono text-slate-300">
                      {((result.probabilities?.negative || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className="bg-rose-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${(result.probabilities?.negative || 0) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Neutral */}
                <div>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-amber-400 font-medium">Neutral</span>
                    <span className="font-mono text-slate-300">
                      {((result.probabilities?.neutral || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className="bg-amber-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${(result.probabilities?.neutral || 0) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Issue Detection Card */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
              <div>
                <h3 className="text-sm font-bold text-white">Rule-Based Issue Detection</h3>
                <p className="text-[11px] text-slate-400">Contextual regex matching across 10 complaint categories with negation guards</p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                Rule Engine
              </span>
            </div>

            {result.issues && result.issues.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                {result.issues.map((issue, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-start justify-between gap-3 text-xs"
                  >
                    <div>
                      <span className="font-semibold text-white block capitalize">{issue.category}</span>
                      <span className="text-slate-400 text-[11px] mt-0.5 block italic">
                        Matched evidence: "{issue.matched_evidence || issue.matched_phrase || issue.evidence || 'keyword match'}"
                      </span>
                    </div>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border shrink-0 ${
                      issue.aspect_sentiment === 'positive'
                        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                        : 'text-rose-400 bg-rose-500/10 border-rose-500/20'
                    }`}>
                      {issue.aspect_sentiment === 'positive' ? 'Positive Aspect' : 'Issue Detected'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-400 text-center italic">
                No predefined issue pattern matched. This does not necessarily mean that the review contains no complaint.
              </div>
            )}
          </div>

          {/* Explainability Section */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
              <div>
                <h3 className="text-sm font-bold text-white">Model Explainability</h3>
                <p className="text-[11px] text-slate-400">Token-level influence on the predicted sentiment</p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-brand-300 border border-slate-800">
                {result.active_model === 'sentiment_baseline' ? 'TF-IDF Linear Attribution' : 'Transformer Attribution Notice'}
              </span>
            </div>

            {result.active_model === 'sentiment_baseline' && result.explanation?.available ? (
              <div className="space-y-4 text-xs">
                <p className="text-slate-300 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800">
                  {result.explanation.summary}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Positive Contributing Tokens */}
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
                    <span className="text-[10px] uppercase font-semibold text-emerald-400 tracking-wider block">
                      Tokens Supporting '{result.sentiment?.toUpperCase()}' Prediction
                    </span>
                    {result.explanation.positive_contributors?.length > 0 ? (
                      <div className="space-y-1.5">
                        {result.explanation.positive_contributors.map((t, idx) => (
                          <div key={idx} className="flex justify-between items-center text-xs">
                            <span className="font-mono text-slate-200">"{t.token}"</span>
                            <span className="font-mono text-emerald-400 font-semibold">+{t.score.toFixed(3)}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-400 italic text-[11px]">No dominant supporting tokens.</span>
                    )}
                  </div>

                  {/* Negative Contributing Tokens */}
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
                    <span className="text-[10px] uppercase font-semibold text-rose-400 tracking-wider block">
                      Tokens Opposing '{result.sentiment?.toUpperCase()}' Prediction
                    </span>
                    {result.explanation.negative_contributors?.length > 0 ? (
                      <div className="space-y-1.5">
                        {result.explanation.negative_contributors.map((t, idx) => (
                          <div key={idx} className="flex justify-between items-center text-xs">
                            <span className="font-mono text-slate-200">"{t.token}"</span>
                            <span className="font-mono text-rose-400 font-semibold">{t.score.toFixed(3)}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-slate-400 italic text-[11px]">No dominant opposing tokens.</span>
                    )}
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 italic border-t border-slate-800/60 pt-2">
                  {result.explanation.disclaimer || 'Linear attribution represents TF-IDF feature weight influence.'}
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-2 leading-relaxed">
                <p className="font-medium text-amber-300">
                  Token-level explanation is currently available for Logistic Regression only. DistilBERT sentiment predictions are shown with their class probabilities.
                </p>
                <p className="text-slate-400 text-[11px]">
                  DistilBERT produces contextual self-attention representations across 6 Transformer layers. To prevent misleading or fabricated feature attributions, linear TF-IDF token weights are not displayed for Transformer predictions. Switch to Logistic Regression above to view token-level linear feature attribution.
                </p>
              </div>
            )}
          </div>

          {/* G. OPTIONAL: CUSTOMER RESPONSE ASSISTANT (COLLAPSED BY DEFAULT) */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <button
              type="button"
              onClick={() => setResponseExpanded((prev) => !prev)}
              className="w-full p-4 flex items-center justify-between hover:bg-slate-800/40 transition text-left"
            >
              <div className="flex items-center gap-2.5">
                <Bot className="w-5 h-5 text-indigo-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">Generate Suggested Customer Response</h3>
                  <p className="text-[11px] text-slate-400">Create a grounded support reply draft without unverified promises</p>
                </div>
              </div>
              {responseExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
            </button>

            {responseExpanded && (
              <div className="p-5 border-t border-slate-800 bg-slate-950/40 space-y-4 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <span className="text-slate-300">
                    Draft a professional reply acknowledging the customer's sentiment ({result.sentiment}) and addressing detected issues.
                  </span>
                  <button
                    type="button"
                    onClick={handleGenerateResponse}
                    disabled={responseGenerating}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold transition shrink-0 flex items-center gap-1.5 self-start sm:self-auto shadow-sm"
                  >
                    {responseGenerating ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Drafting Response...</span>
                      </>
                    ) : (
                      <>
                        <Bot className="w-3.5 h-3.5" />
                        <span>Draft Response</span>
                      </>
                    )}
                  </button>
                </div>

                {generatedResponseText && (
                  <div className="space-y-3 pt-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase font-semibold text-slate-400">
                        Suggested Draft ({responseMeta?.mode === 'gemini_grounded' ? 'Gemini 2.5 Grounded' : 'Deterministic Template'})
                      </span>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(generatedResponseText);
                          setCopiedResponse(true);
                          setTimeout(() => setCopiedResponse(false), 2000);
                        }}
                        className="text-brand-400 hover:text-brand-300 inline-flex items-center gap-1 text-[11px]"
                      >
                        {copiedResponse ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedResponse ? 'Copied' : 'Copy Response'}</span>
                      </button>
                    </div>

                    <textarea
                      rows={4}
                      value={generatedResponseText}
                      onChange={(e) => setGeneratedResponseText(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-slate-200 leading-relaxed text-xs focus:outline-none focus:border-indigo-500"
                    />

                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-[11px] text-amber-300/90 space-y-1">
                      <strong>Policy Guardrail Disclaimer:</strong> AI-generated responses are drafts and should be reviewed before being sent. Never promise unverified refunds, replacements, or delivery dates without human authorization.
                    </div>

                    {/* H. OPTIONAL: RESPONSE SAFETY CHECK (COLLAPSED UNDER RESPONSE) */}
                    <div className="border border-slate-800 rounded-xl overflow-hidden mt-3 bg-slate-900/60">
                      <button
                        type="button"
                        onClick={() => setSafetyExpanded((prev) => !prev)}
                        className="w-full p-3.5 flex items-center justify-between hover:bg-slate-850/60 transition text-left"
                      >
                        <div className="flex items-center gap-2">
                          <ShieldCheck className="w-4 h-4 text-emerald-400" />
                          <span className="font-semibold text-white text-xs">
                            Check Response Against Customer Feedback (Experimental Evidence Screening)
                          </span>
                        </div>
                        {safetyExpanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
                      </button>

                      {safetyExpanded && (
                        <div className="p-4 border-t border-slate-800 space-y-3 bg-slate-950/60">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <p className="text-slate-400 text-[11px]">
                              Decomposes the draft response into factual claims and verifies them against the customer's text.
                            </p>
                            <button
                              type="button"
                              onClick={handleRunSafetyCheck}
                              disabled={screeningLoading}
                              className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded text-[11px] font-medium transition self-start sm:self-auto shrink-0"
                            >
                              {screeningLoading ? 'Screening Claims...' : 'Run Evidence Check'}
                            </button>
                          </div>

                          {verificationResult && (
                            <div className="space-y-3 pt-2 text-xs">
                              <div className="grid grid-cols-3 gap-2 text-center font-mono text-[11px]">
                                <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                                  Supported: {verificationResult.supported_count}
                                </div>
                                <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300">
                                  Contradicted: {verificationResult.contradicted_count}
                                </div>
                                <div className="p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300">
                                  Unsupported: {verificationResult.unsupported_count}
                                </div>
                              </div>

                              <div className="space-y-2">
                                {verificationResult.claims?.map((item, idx) => (
                                  <div
                                    key={idx}
                                    className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1.5"
                                  >
                                    <div className="flex items-center justify-between">
                                      <span className="font-semibold text-white">Claim {idx + 1}: "{item.claim_text}"</span>
                                      <span
                                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                          item.status === 'SUPPORTED'
                                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                            : item.status === 'CONTRADICTED'
                                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                        }`}
                                      >
                                        {item.status}
                                      </span>
                                    </div>
                                    <p className="text-slate-400 text-[11px]">{item.explanation}</p>
                                    {item.supporting_evidence && item.supporting_evidence.length > 0 && (
                                      <div className="text-[10px] text-slate-400 font-mono">
                                        Evidence: "{item.supporting_evidence[0]}"
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>

                              <div className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-800">
                                Notice: This evidence screening uses heuristic phrase matching and semantic overlap. It does not employ an NLI model and does not guarantee complete hallucination prevention.
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
