import React, { useState } from 'react';
import { api } from '../services/api';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { Shield, Lock, EyeOff, CheckCircle2, Send, MessageSquare } from 'lucide-react';

export const PrivacyPage: React.FC = () => {
  const [feedbackCategory, setFeedbackCategory] = useState('general');
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [schemeSlug, setSchemeSlug] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackMessage.trim()) return;
    setIsSubmitting(true);
    try {
      await api.submitFeedback({
        category: feedbackCategory,
        scheme_slug: schemeSlug || undefined,
        message: feedbackMessage.trim()
      });
      setFeedbackSuccess(true);
      setFeedbackMessage('');
      setSchemeSlug('');
      setTimeout(() => setFeedbackSuccess(false), 5000);
    } catch (err: any) {
      alert('Error submitting report: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-softmint text-leaf-800 text-xs font-bold border border-leaf-200">
          <Shield className="w-3.5 h-3.5" />
          <span>Citizen Privacy Charter</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-900 tracking-tight">
          Privacy, Security & Data Protection Charter
        </h1>
        <p className="text-sm sm:text-base text-navy-700/80">
          How JanSahayak protects citizen information, enforces strict data isolation, and respects citizen digital rights.
        </p>
      </div>

      {/* Core Privacy Principles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-leaf-100 text-leaf-800 flex items-center justify-center">
            <EyeOff className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-navy-900">Zero Sensitive ID Policy</h3>
          <p className="text-xs text-navy-700/80 leading-relaxed">
            We never request, store, or process Aadhaar numbers, biometric data, PAN cards, or banking passwords. Eligibility checks use only abstract qualifiers.
          </p>
        </Card>

        <Card className="p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-softsky text-blue-800 flex items-center justify-center">
            <Lock className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-navy-900">Strict Citizen Data Isolation</h3>
          <p className="text-xs text-navy-700/80 leading-relaxed">
            Every database query is bound to your cryptographic session. No citizen can ever access, modify, or view drafts saved by another person.
          </p>
        </Card>

        <Card className="p-6 space-y-3">
          <div className="w-10 h-10 rounded-xl bg-saffron-100 text-saffron-800 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-navy-900">Full Right to Erasure</h3>
          <p className="text-xs text-navy-700/80 leading-relaxed">
            You own your information. You can delete individual drafts at any time, or permanently erase your entire account from your Citizen Dashboard.
          </p>
        </Card>
      </div>

      {/* Detailed Policy Text */}
      <Card className="p-6 sm:p-8 space-y-4 text-sm text-navy-800 leading-relaxed">
        <h3 className="font-bold text-lg text-navy-900">1. Information We Collect and Why</h3>
        <p>
          JanSahayak collects only the minimal data required to provide welfare discovery and application preparation services:
        </p>
        <ul className="list-disc pl-5 space-y-1 text-xs text-navy-700">
          <li>Account credentials (name, email, and salted cryptographic password hash).</li>
          <li>User preferences such as state of residence and language choice.</li>
          <li>Welfare application drafts and RTI notes explicitly saved by you.</li>
        </ul>

        <h3 className="font-bold text-lg text-navy-900 pt-2">2. No AI Training on Citizen Records</h3>
        <p>
          Any question you submit to the multilingual voice or text assistant is processed ephemerally to retrieve matching passages from verified government documentation. Your queries and saved drafts are never used to train commercial AI models.
        </p>

        <h3 className="font-bold text-lg text-navy-900 pt-2">3. Deterministic Non-Hallucinatory Rules</h3>
        <p>
          We do not allow generative language models to invent eligibility criteria or promise official approvals. All qualification checks are computed deterministically in Python against codified government criteria.
        </p>
      </Card>

      {/* Citizen Feedback & Inaccuracy Reporting Form */}
      <Card className="p-6 sm:p-8 space-y-4 border-leaf-200 bg-softmint/20">
        <div className="space-y-1">
          <h3 className="font-bold text-lg text-navy-900 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-leaf-700" />
            <span>Report Broken Links or Outdated Information</span>
          </h3>
          <p className="text-xs text-navy-700/80">
            Notice an expired scheme guideline, broken portal link, or translation issue? Report it directly to our verification team.
          </p>
        </div>

        {feedbackSuccess && (
          <Alert type="success">
            Thank you for your report! Our administrative team will review and update the scheme record.
          </Alert>
        )}

        <form onSubmit={handleFeedbackSubmit} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Report Category
              </label>
              <select
                value={feedbackCategory}
                onChange={(e) => setFeedbackCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              >
                <option value="broken_link">Broken Official Portal Link</option>
                <option value="outdated_info">Outdated Eligibility Rule or Benefit Amount</option>
                <option value="translation_error">Regional Language Translation Issue</option>
                <option value="general">General Suggestion or Feedback</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-navy-900 mb-1">
                Related Scheme Slug (Optional)
              </label>
              <input
                type="text"
                value={schemeSlug}
                onChange={(e) => setSchemeSlug(e.target.value)}
                placeholder="e.g. pm-kisan, pmay-g"
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-navy-900 mb-1">
              Description of the Issue
            </label>
            <textarea
              rows={3}
              required
              value={feedbackMessage}
              onChange={(e) => setFeedbackMessage(e.target.value)}
              placeholder="Describe what appears incorrect or broken..."
              className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={isSubmitting}
            leftIcon={<Send className="w-4 h-4" />}
          >
            Submit Report
          </Button>
        </form>
      </Card>

    </div>
  );
};
