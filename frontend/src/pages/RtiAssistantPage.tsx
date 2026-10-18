import React, { useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import {
  FileText,
  Download,
  Save,
  ExternalLink,
  ShieldAlert,
  Info,
  CheckCircle,
  HelpCircle
} from 'lucide-react';

export const RtiAssistantPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();

  const [formData, setFormData] = useState({
    public_authority: 'Department of Agriculture & Farmers Welfare',
    subject: 'Status and Reason for Delay of PM-KISAN Installment Release',
    information_requested:
      "1. Please provide the certified current status of my PM-KISAN application / beneficiary record.\n" +
      "2. State the specific administrative or verification reason why the recent installment has not been credited.\n" +
      "3. Provide copies of any field verification or revenue department inquiry reports conducted in this matter.\n" +
      "4. State the name and designation of the public official responsible for resolving this pendency.",
    time_period: 'Financial Year 2025-2026',
    applicant_name: user?.full_name || '',
    state: user?.state || 'Uttar Pradesh',
    preferred_language: 'en'
  });

  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [savedDraftId, setSavedDraftId] = useState<number | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const handleSaveDraft = async () => {
    if (!isAuthenticated) {
      alert('Please log in to save your RTI draft to your dashboard.');
      return;
    }
    setIsSaving(true);
    try {
      const res = await api.createRtiDraft(formData);
      setSavedDraftId(res.id);
      setNotification({ type: 'success', message: 'RTI draft saved successfully to your Citizen Dashboard!' });
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to save RTI draft.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      let draftId = savedDraftId;
      if (!draftId) {
        // If not already saved in db, save draft first or require login
        if (isAuthenticated) {
          const res = await api.createRtiDraft(formData);
          draftId = res.id;
          setSavedDraftId(res.id);
        } else {
          alert('Please create a free citizen account or log in to generate your official signed RTI PDF.');
          setIsDownloading(false);
          return;
        }
      }

      if (!draftId) return;
      const blob = await api.downloadRtiPdf(draftId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `RTI_Application_${draftId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert('Error generating RTI PDF: ' + err.message);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-softsky text-blue-900 text-xs font-bold border border-blue-200">
          <FileText className="w-3.5 h-3.5 text-blue-700" />
          <span>Section 6(1), Right to Information Act, 2005</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-900 tracking-tight">
          RTI Application Drafting Assistant
        </h1>
        <p className="text-sm sm:text-base text-navy-700/80">
          Draft a legally structured RTI petition to obtain official records, reasons for delays, and certified inspection reports.
        </p>
      </div>

      {/* Distinction Alert */}
      <Alert type="info" title="What an RTI Request Does (and Does Not) Do:">
        <p>
          <b>Valid RTI:</b> Requests for existing public records, certified file copies, status reports, and official reasons documented in government files.<br/>
          <b>Not an RTI:</b> General complaints, demands to overturn judicial decisions, or requests for opinions. If you want administrative action or grievance redressal, please use the <a href="/grievances" className="font-bold underline text-blue-900">Public Grievance Assistant</a> instead.
        </p>
      </Alert>

      {notification && (
        <Alert type={notification.type}>{notification.message}</Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Form: Form Inputs (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <Card className="p-6 space-y-4">
            
            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Target Public Authority / Department
              </label>
              <input
                type="text"
                value={formData.public_authority}
                onChange={(e) => setFormData({ ...formData, public_authority: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                placeholder="e.g. Ministry of Rural Development / District Magistrate Office"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Subject of the Information Request
              </label>
              <input
                type="text"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Applicant Name
                </label>
                <input
                  type="text"
                  value={formData.applicant_name}
                  onChange={(e) => setFormData({ ...formData, applicant_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  State / Territory
                </label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Relevant Time Period
              </label>
              <input
                type="text"
                value={formData.time_period}
                onChange={(e) => setFormData({ ...formData, time_period: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                placeholder="e.g. April 2025 to March 2026"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Specific Information & Records Solicited
              </label>
              <textarea
                rows={6}
                value={formData.information_requested}
                onChange={(e) => setFormData({ ...formData, information_requested: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-xs sm:text-sm font-mono leading-relaxed focus:border-leaf-600 focus:outline-none"
              />
              <span className="text-[11px] text-navy-700/60 mt-1 block">
                Number each point clearly (1, 2, 3) for clarity before the Public Information Officer.
              </span>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row gap-2">
              <Button
                variant="primary"
                size="md"
                onClick={handleSaveDraft}
                isLoading={isSaving}
                leftIcon={<Save className="w-4 h-4" />}
                className="w-full sm:w-1/2"
              >
                Save RTI Draft
              </Button>
              <Button
                variant="secondary"
                size="md"
                onClick={handleDownloadPdf}
                isLoading={isDownloading}
                leftIcon={<Download className="w-4 h-4" />}
                className="w-full sm:w-1/2"
              >
                Download PDF
              </Button>
            </div>

          </Card>
        </div>

        {/* Right Output: Live Petition Preview (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <Card className="p-6 bg-ivory-50/50 border border-ivory-200 space-y-4 font-serif text-navy-950 text-xs sm:text-sm leading-relaxed shadow-sm">
            <div className="text-center border-b border-ivory-300 pb-3 space-y-1">
              <span className="font-bold text-xs uppercase tracking-wider text-navy-800">
                Application Under Section 6(1)
              </span>
              <h3 className="font-bold text-base text-navy-950">
                Right to Information Act, 2005
              </h3>
            </div>

            <div className="space-y-1 text-xs">
              <p><b>To:</b> The Public Information Officer (PIO)</p>
              <p><b>Department:</b> {formData.public_authority || '[Target Public Authority]'}</p>
              <p><b>State:</b> {formData.state || '[State]'}</p>
            </div>

            <div className="space-y-1 text-xs pt-1">
              <p><b>Applicant Name:</b> {formData.applicant_name || '[Applicant Name]'}</p>
              <p><b>Citizenship:</b> Citizen of India</p>
              <p><b>Subject:</b> {formData.subject}</p>
              {formData.time_period && <p><b>Period:</b> {formData.time_period}</p>}
            </div>

            <div className="space-y-1.5 pt-2 border-t border-ivory-200">
              <p className="font-bold">Information Solicited:</p>
              <p className="whitespace-pre-wrap font-sans text-xs bg-white p-3 rounded-xl border border-ivory-200">
                {formData.information_requested}
              </p>
            </div>

            <div className="pt-2 text-[11px] text-navy-700/80 leading-snug">
              <p>
                <b>Statutory Fee:</b> Application fee of Rs. 10/- attached as prescribed under RTI Rules.
              </p>
            </div>

            <div className="pt-4 border-t border-ivory-200 flex justify-between text-xs font-sans text-navy-700">
              <span>Date: {new Date().toLocaleDateString()}</span>
              <span>Signature: __________________</span>
            </div>
          </Card>

          {/* Submission Instructions */}
          <div className="p-4 rounded-xl bg-white border border-ivory-200 text-xs text-navy-800 space-y-2">
            <h5 className="font-bold flex items-center gap-1.5 text-leaf-800">
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Official Submission Options:</span>
            </h5>
            <ol className="list-decimal pl-4 space-y-1 text-navy-700/90">
              <li>
                <b>Central Govt Ministries:</b> File online at <a href="https://rtionline.gov.in" target="_blank" rel="noopener noreferrer" className="font-bold underline text-blue-900">rtionline.gov.in</a> (Fee: ₹10 net banking/UPI).
              </li>
              <li>
                <b>State Departments:</b> Print the PDF, affix a ₹10 Court Fee Stamp or Indian Postal Order (IPO), and submit at the local PIO office or Speed Post.
              </li>
            </ol>
          </div>
        </div>

      </div>

    </div>
  );
};
