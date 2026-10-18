import React, { useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import {
  AlertCircle,
  Download,
  Save,
  ExternalLink,
  ShieldAlert,
  Send,
  Building,
  HelpCircle
} from 'lucide-react';

export const GrievanceAssistantPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();

  const [formData, setFormData] = useState({
    department: 'Department of Rural Development',
    category: 'Delayed Installment Sanction',
    description:
      "I was verified and listed as eligible under PMAY-G in the Gram Sabha list. " +
      "Geo-tagging of my kutcha house was completed three months ago by the Gram Panchayat Secretary. " +
      "However, the first installment of ₹40,000 has not been released into my bank account, and no written reason has been provided.",
    previous_complaint_ref: 'TKN/2026/89421',
    desired_resolution: 'Immediate release of the first construction installment and updated sanction order.',
    applicant_name: user?.full_name || ''
  });

  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [savedDraftId, setSavedDraftId] = useState<number | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const handleSaveDraft = async () => {
    if (!isAuthenticated) {
      alert('Please log in to save your grievance draft to your Citizen Dashboard.');
      return;
    }
    setIsSaving(true);
    try {
      const res = await api.createGrievanceDraft(formData);
      setSavedDraftId(res.id);
      setNotification({ type: 'success', message: 'Grievance draft successfully saved to your Citizen Dashboard!' });
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to save grievance.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    try {
      let draftId = savedDraftId;
      if (!draftId) {
        if (isAuthenticated) {
          const res = await api.createGrievanceDraft(formData);
          draftId = res.id;
          setSavedDraftId(res.id);
        } else {
          alert('Please log in or register to generate your official Grievance PDF.');
          setIsDownloading(false);
          return;
        }
      }

      if (!draftId) return;
      const blob = await api.downloadGrievancePdf(draftId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Public_Grievance_Petition_${draftId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert('Error generating Grievance PDF: ' + err.message);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-saffron-50 text-saffron-700 text-xs font-bold border border-saffron-200">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>Public Grievance Redressal Mechanism</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-900 tracking-tight">
          Public Grievance Drafter
        </h1>
        <p className="text-sm sm:text-base text-navy-700/80">
          Prepare a clear, structured grievance for CPGRAMS or state portals addressing service delays, portal glitches, or arbitrary rejections.
        </p>
      </div>

      {notification && (
        <Alert type={notification.type}>{notification.message}</Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Inputs (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <Card className="p-6 space-y-4">
            
            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Target Government Department
              </label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Grievance Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              >
                <option value="Delayed Installment Sanction">Delayed Installment / Payment Sanction</option>
                <option value="Application Pending Verification">Application Pending Field Verification</option>
                <option value="Aadhaar / Bank Seeding Failure">Aadhaar / Bank Seeding Failure</option>
                <option value="Document Rejection Without Reason">Document Rejection Without Specific Reason</option>
                <option value="Ration Card / SECC Data Inconsistency">Ration Card / SECC Data Inconsistency</option>
                <option value="Harassment or Demand for Illegal Gratification">Harassment or Procedural Delay</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-navy-900 mb-1">
                  Complainant Full Name
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
                  Previous Token / Ref (Optional)
                </label>
                <input
                  type="text"
                  value={formData.previous_complaint_ref}
                  onChange={(e) => setFormData({ ...formData, previous_complaint_ref: e.target.value })}
                  placeholder="e.g. CPGRAMS Token"
                  className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Factual Chronological Description
              </label>
              <textarea
                rows={5}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-xs sm:text-sm leading-relaxed focus:border-leaf-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Specific Relief or Resolution Sought
              </label>
              <textarea
                rows={3}
                value={formData.desired_resolution}
                onChange={(e) => setFormData({ ...formData, desired_resolution: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-xs sm:text-sm leading-relaxed focus:border-leaf-600 focus:outline-none"
              />
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
                Save Grievance Draft
              </Button>
              <Button
                variant="secondary"
                size="md"
                onClick={handleDownloadPdf}
                isLoading={isDownloading}
                leftIcon={<Download className="w-4 h-4" />}
                className="w-full sm:w-1/2"
              >
                Export PDF
              </Button>
            </div>

          </Card>
        </div>

        {/* Right Preview (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <Card className="p-6 bg-ivory-50/50 border border-ivory-200 space-y-4 text-xs sm:text-sm leading-relaxed shadow-sm">
            <div className="text-center border-b border-ivory-300 pb-3 space-y-1">
              <span className="font-bold text-xs uppercase tracking-wider text-saffron-700">
                Official Public Grievance Representation
              </span>
              <h3 className="font-bold text-base text-navy-950">
                Citizen Redressal Memorandum
              </h3>
            </div>

            <div className="space-y-1 text-xs">
              <p><b>Target Department:</b> {formData.department}</p>
              <p><b>Category:</b> {formData.category}</p>
              <p><b>Complainant Name:</b> {formData.applicant_name || '[Applicant Name]'}</p>
              {formData.previous_complaint_ref && (
                <p><b>Previous Reference / Token:</b> {formData.previous_complaint_ref}</p>
              )}
            </div>

            <div className="space-y-1.5 pt-2 border-t border-ivory-200 text-xs">
              <p className="font-bold text-navy-950">Factual Narrative:</p>
              <p className="whitespace-pre-wrap bg-white p-3 rounded-xl border border-ivory-200">
                {formData.description}
              </p>
            </div>

            <div className="space-y-1.5 pt-2 border-t border-ivory-200 text-xs">
              <p className="font-bold text-navy-950">Resolution Demanded:</p>
              <p className="whitespace-pre-wrap bg-white p-3 rounded-xl border border-ivory-200 text-leaf-950 font-medium">
                {formData.desired_resolution}
              </p>
            </div>

            <div className="pt-4 border-t border-ivory-200 flex justify-between text-xs text-navy-700">
              <span>Date: {new Date().toLocaleDateString()}</span>
              <span>Signature: __________________</span>
            </div>
          </Card>

          {/* Submission Instructions */}
          <div className="p-4 rounded-xl bg-white border border-ivory-200 text-xs text-navy-800 space-y-2">
            <h5 className="font-bold flex items-center gap-1.5 text-leaf-800">
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Official Lodging Portals:</span>
            </h5>
            <ol className="list-decimal pl-4 space-y-1 text-navy-700/90">
              <li>
                <b>CPGRAMS (Centralised Public Grievance Redress and Monitoring System):</b> Lodge online at <a href="https://pgportal.gov.in" target="_blank" rel="noopener noreferrer" className="font-bold underline text-blue-900">pgportal.gov.in</a>.
              </li>
              <li>
                <b>State Portals:</b> CM Helpline / Jan Seva Kendra (e.g. UP Jansunwai - jansunwai.up.nic.in, Bihar Lok Shikayat, Maharashtra Aaple Sarkar).
              </li>
            </ol>
          </div>
        </div>

      </div>

    </div>
  );
};
