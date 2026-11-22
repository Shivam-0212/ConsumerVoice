import axios from 'axios';

const baseURL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const fetchHealth = () => api.get('/health').then(res => res.data);
export const fetchDashboardOverview = () => api.get('/dashboard/overview').then(res => res.data);
export const fetchDashboardSentiment = () => api.get('/dashboard/sentiment').then(res => res.data);
export const fetchDashboardIssues = () => api.get('/dashboard/issues').then(res => res.data);

export const fetchReviews = (params) => api.get('/reviews', { params }).then(res => res.data);
export const fetchReviewDetail = (id) => api.get(`/reviews/${id}`).then(res => res.data);
export const analyzeReview = (payload) => api.post('/reviews/analyze', payload).then(res => res.data);

export const generateSummary = (payload) => api.post('/summaries/generate', payload).then(res => res.data);
export const generateResponse = (payload) => api.post('/responses/generate', payload).then(res => res.data);
export const verifyResponse = (payload) => api.post('/responses/verify', payload).then(res => res.data);

export const fetchEvaluations = () => api.get('/evaluations').then(res => res.data);
export const setActiveModel = (modelName) => api.post('/evaluations/active-model', { model_name: modelName }).then(res => res.data);
export const fetchDatasetQuality = () => api.get('/dataset/quality').then(res => res.data);

export default api;

