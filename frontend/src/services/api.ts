const getApiBase = (): string => {
  let base = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api').trim().replace(/\/+$/, '');
  if (!base.endsWith('/api')) {
    base = `${base}/api`;
  }
  return base;
};

const API_BASE = getApiBase();

class ApiClient {
  private getHeaders(): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = localStorage.getItem('jansahayak_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers = { ...this.getHeaders(), ...(options.headers || {}) };

    try {
      const response = await fetch(url, { ...options, headers });
      
      if (!response.ok) {
        let errorMessage = `Request failed with status ${response.status}`;
        try {
          const errData = await response.json();
          if (errData && errData.detail) {
            errorMessage = errData.detail;
          }
        } catch (_) {
          // If response not JSON, keep default
        }
        throw new Error(errorMessage);
      }

      // If empty response (e.g. 204 or delete message)
      const text = await response.text();
      return text ? JSON.parse(text) : ({} as T);
    } catch (error: any) {
      if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
        throw new Error('Unable to connect to JanSahayak service. Please check your network connection.');
      }
      throw error;
    }
  }

  // --- Auth ---
  register(data: any) {
    return this.request<any>('/auth/register', { method: 'POST', body: JSON.stringify(data) });
  }

  login(data: any) {
    return this.request<any>('/auth/login', { method: 'POST', body: JSON.stringify(data) });
  }

  logout() {
    return this.request<any>('/auth/logout', { method: 'POST' });
  }

  getMe() {
    return this.request<any>('/auth/me');
  }

  updateProfile(data: any) {
    return this.request<any>('/auth/me', { method: 'PUT', body: JSON.stringify(data) });
  }

  deleteAccount() {
    return this.request<any>('/auth/me', { method: 'DELETE' });
  }

  // --- Schemes ---
  getSchemes(params?: { category?: string; state?: string; scope?: string; beneficiary?: string; q?: string }) {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v && v !== 'all') query.append(k, v);
      });
    }
    const qStr = query.toString();
    return this.request<any[]>(`/schemes${qStr ? `?${qStr}` : ''}`);
  }

  getCategories() {
    return this.request<any[]>('/schemes/categories');
  }

  getScheme(slug: string) {
    return this.request<any>(`/schemes/${slug}`);
  }

  compareSchemes(slugs: string[]) {
    return this.request<any[]>(`/schemes/compare?slugs=${encodeURIComponent(slugs.join(','))}`);
  }

  // --- Eligibility ---
  assessEligibility(schemeSlug: string, profile: any) {
    return this.request<any>('/eligibility/assess', {
      method: 'POST',
      body: JSON.stringify({ scheme_slug: schemeSlug, profile })
    });
  }

  getAssessmentHistory() {
    return this.request<any[]>('/eligibility/history');
  }

  async downloadReportPdf(schemeSlug: string, profile: any): Promise<Blob> {
    const url = `${API_BASE}/eligibility/download-report`;
    const res = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ scheme_slug: schemeSlug, profile })
    });
    if (!res.ok) throw new Error('Failed to generate report PDF');
    return res.blob();
  }

  // --- Assistant & RAG ---
  chatAssistant(query: string, schemeSlug?: string, preferredLanguage: string = 'en') {
    return this.request<any>('/assistant/chat', {
      method: 'POST',
      body: JSON.stringify({ query, scheme_slug: schemeSlug, preferred_language: preferredLanguage })
    });
  }

  // --- Voice & Bhashini ---
  getVoiceStatus() {
    return this.request<any>('/voice/status');
  }

  getLanguages() {
    return this.request<any[]>('/voice/languages');
  }

  // --- Applications ---
  getApplicationDrafts() {
    return this.request<any[]>('/applications');
  }

  createApplicationDraft(data: any) {
    return this.request<any>('/applications', { method: 'POST', body: JSON.stringify(data) });
  }

  getApplicationDraft(id: number) {
    return this.request<any>(`/applications/${id}`);
  }

  updateApplicationDraft(id: number, data: any) {
    return this.request<any>(`/applications/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  deleteApplicationDraft(id: number) {
    return this.request<any>(`/applications/${id}`, { method: 'DELETE' });
  }

  async downloadApplicationPdf(id: number): Promise<Blob> {
    const res = await fetch(`${API_BASE}/applications/${id}/pdf`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to generate application PDF');
    return res.blob();
  }

  // --- RTI ---
  getRtiDrafts() {
    return this.request<any[]>('/rti');
  }

  createRtiDraft(data: any) {
    return this.request<any>('/rti', { method: 'POST', body: JSON.stringify(data) });
  }

  getRtiDraft(id: number) {
    return this.request<any>(`/rti/${id}`);
  }

  updateRtiDraft(id: number, data: any) {
    return this.request<any>(`/rti/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  deleteRtiDraft(id: number) {
    return this.request<any>(`/rti/${id}`, { method: 'DELETE' });
  }

  async downloadRtiPdf(id: number): Promise<Blob> {
    const res = await fetch(`${API_BASE}/rti/${id}/pdf`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to generate RTI PDF');
    return res.blob();
  }

  // --- Grievances ---
  getGrievanceDrafts() {
    return this.request<any[]>('/grievances');
  }

  createGrievanceDraft(data: any) {
    return this.request<any>('/grievances', { method: 'POST', body: JSON.stringify(data) });
  }

  getGrievanceDraft(id: number) {
    return this.request<any>(`/grievances/${id}`);
  }

  updateGrievanceDraft(id: number, data: any) {
    return this.request<any>(`/grievances/${id}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  deleteGrievanceDraft(id: number) {
    return this.request<any>(`/grievances/${id}`, { method: 'DELETE' });
  }

  async downloadGrievancePdf(id: number): Promise<Blob> {
    const res = await fetch(`${API_BASE}/grievances/${id}/pdf`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to generate Grievance PDF');
    return res.blob();
  }

  // --- Dashboard ---
  getDashboardStats() {
    return this.request<any>('/dashboard/stats');
  }

  getSavedSchemes() {
    return this.request<any[]>('/dashboard/saved-schemes');
  }

  toggleSaveScheme(schemeId: number) {
    return this.request<any>(`/dashboard/saved-schemes/${schemeId}`, { method: 'POST' });
  }

  // --- Feedback ---
  submitFeedback(data: any) {
    return this.request<any>('/feedback', { method: 'POST', body: JSON.stringify(data) });
  }

  // --- Admin ---
  adminGetSchemes() {
    return this.request<any[]>('/admin/schemes');
  }

  adminVerifyScheme(schemeId: number, data: any) {
    return this.request<any>(`/admin/schemes/${schemeId}/verify`, { method: 'PUT', body: JSON.stringify(data) });
  }

  adminGetAuditLogs() {
    return this.request<any[]>('/admin/audit-logs');
  }

  adminGetFeedbacks() {
    return this.request<any[]>('/admin/feedbacks');
  }
}

export const api = new ApiClient();
