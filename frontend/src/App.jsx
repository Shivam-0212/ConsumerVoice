import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import OverviewDashboard from './pages/OverviewDashboard';
import ReviewExplorer from './pages/ReviewExplorer';
import AIReviewAnalysis from './pages/AIReviewAnalysis';
import ModelLab from './pages/ModelLab';

export default function App() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* Four Primary Pages */}
          <Route index element={<OverviewDashboard />} />
          <Route path="explorer" element={<ReviewExplorer />} />
          <Route path="analyze" element={<AIReviewAnalysis />} />
          <Route path="models" element={<ModelLab />} />

          {/* Legacy and Deprecated Route Redirects */}
          <Route path="guide" element={<Navigate to="/" replace />} />
          <Route path="summarization" element={<Navigate to="/explorer" replace />} />
          <Route path="response-generator" element={<Navigate to="/analyze" replace />} />
          <Route path="hallucination" element={<Navigate to="/analyze" replace />} />
          <Route path="dataset" element={<Navigate to="/" replace />} />
          <Route path="methodology" element={<Navigate to="/" replace />} />

          {/* Fallback to Dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
