import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Scheme } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Alert } from '../components/common/Alert';
import { useAuth } from '../context/AuthContext';
import {
  FileText,
  CheckCircle2,
  Download,
  Save,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  Check,
  X
} from 'lucide-react';

export const ApplicationPrepPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const preselectedSlug = searchParams.get('scheme') || 'pm-kisan';
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [applicantName, setApplicantName] = useState(user?.full_name || '');
  const [notes, setNotes] = useState('');
  const [checklist, setChecklist] = useState<Record<string, boolean>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const scs = await api.getSchemes();
        setSchemes(scs);
        const current = scs.find((s) => s.slug === preselectedSlug) || scs[0];
        if (current) {
          setSelectedScheme(current);
          // Initialize checklist
          const initCheck: Record<string, boolean> = {};
          current.required_documents?.forEach((d: any) => {
            initCheck[d.name] = false;
          });
          setChecklist(initCheck);
        }
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, [preselectedSlug]);

  const handleSchemeChange = (slug: string) => {
    const sc = schemes.find((s) => s.slug === slug);
    if (sc) {
      setSelectedScheme(sc);
      const initCheck: Record<string, boolean> = {};
      sc.required_documents?.forEach((d: any) => {
        initCheck[d.name] = false;
      });
      setChecklist(initCheck);
    }
  };

  const toggleDoc = (name: string) => {
    setChecklist((prev) => ({
      ...prev,
      [name]: !prev[name]
    }));
  };

  const handleSaveDraft = async () => {
    if (!isAuthenticated) {
      alert('Please log in or register to save your draft to your Citizen Dashboard.');
      navigate('/login');
      return;
    }
    if (!selectedScheme) return;
    setIsSaving(true);
    try {
      await api.createApplicationDraft({
        scheme_id: selectedScheme.id,
        title: `${selectedScheme.name} Draft - ${applicantName || 'Citizen'}`,
        applicant_details: { applicant_name: applicantName },
        checklist_state: checklist,
        notes: notes
      });
      setNotification({ type: 'success', message: 'Application draft successfully saved to your Citizen Dashboard!' });
      setTimeout(() => setNotification(null), 4000);
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to save draft.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadChecklist = async () => {
    if (!selectedScheme) return;
    setIsDownloading(true);
    try {
      const blob = await api.downloadReportPdf(selectedScheme.slug, {
        applicant_name: applicantName,
        notes: notes
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Application_Checklist_${selectedScheme.slug}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert('Failed to generate PDF: ' + err.message);
    } finally {
      setIsDownloading(false);
    }
  };

  const totalDocs = selectedScheme?.required_documents?.length || 0;
  const readyDocs = Object.values(checklist).filter(Boolean).length;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-softmint text-leaf-800 text-xs font-bold border border-leaf-200">
          <FileText className="w-3.5 h-3.5" />
          <span>Application Preparation Workspace</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-900 tracking-tight">
          Prepare Your Application & Documents
        </h1>
        <p className="text-sm sm:text-base text-navy-700/80">
          Ensure all verified documents are ready with accepted alternatives before applying on the official portal.
        </p>
      </div>

      {notification && (
        <Alert type={notification.type}>{notification.message}</Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left: Scheme selection & Applicant details (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="p-6 space-y-4">
            
            <div>
              <label className="block text-xs font-bold uppercase text-navy-900 mb-1.5">
                Target Welfare Scheme
              </label>
              <select
                value={selectedScheme?.slug || ''}
                onChange={(e) => handleSchemeChange(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-ivory-300 text-sm font-semibold text-navy-900 bg-ivory-50 focus:border-leaf-600 focus:outline-none"
              >
                {schemes.map((s) => (
                  <option key={s.slug} value={s.slug}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-800 mb-1">
                Applicant Full Name
              </label>
              <input
                type="text"
                value={applicantName}
                onChange={(e) => setApplicantName(e.target.value)}
                placeholder="Full name as written on primary ID"
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-navy-800 mb-1">
                Personal Application Notes / Token Ref
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Visited CSC on 12th Oct; Patta document submitted for verification."
                className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
              />
            </div>

            {/* Document Readiness Progress Bar */}
            <div className="p-4 rounded-xl bg-ivory-50 border border-ivory-200 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-navy-900">
                <span>Document Readiness</span>
                <span className="text-leaf-700">{readyDocs} of {totalDocs} Ready</span>
              </div>
              <div className="w-full h-2 rounded-full bg-ivory-200 overflow-hidden">
                <div
                  className="h-full bg-leaf-700 transition-all duration-300"
                  style={{ width: `${totalDocs ? (readyDocs / totalDocs) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div className="space-y-2 pt-2">
              <Button
                variant="primary"
                size="md"
                onClick={handleSaveDraft}
                isLoading={isSaving}
                leftIcon={<Save className="w-4 h-4" />}
                className="w-full"
              >
                Save Draft to Dashboard
              </Button>
              <Button
                variant="outline"
                size="md"
                onClick={handleDownloadChecklist}
                isLoading={isDownloading}
                leftIcon={<Download className="w-4 h-4" />}
                className="w-full"
              >
                Export Printable Checklist PDF
              </Button>
            </div>

          </Card>
        </div>

        {/* Right: Document Checklist and Alternatives (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <Card className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-base text-navy-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-leaf-700" />
                <span>Verified Mandatory Documents & Official Alternatives</span>
              </h3>
            </div>

            <p className="text-xs text-navy-700/70">
              Click the checkbox next to each document once you have verified its availability.
            </p>

            <div className="space-y-3 pt-2">
              {selectedScheme?.required_documents?.map((doc, idx) => {
                const isReady = !!checklist[doc.name];
                return (
                  <div
                    key={idx}
                    onClick={() => toggleDoc(doc.name)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isReady
                        ? 'bg-softmint/60 border-leaf-300 shadow-sm'
                        : 'bg-white border-ivory-200 hover:border-ivory-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div
                          className={`w-5 h-5 rounded-md flex items-center justify-center shrink-0 mt-0.5 border ${
                            isReady
                              ? 'bg-leaf-700 text-white border-leaf-700'
                              : 'border-ivory-300 bg-white'
                          }`}
                        >
                          {isReady && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                        </div>
                        <div>
                          <span className={`text-sm font-bold ${isReady ? 'text-leaf-950' : 'text-navy-900'}`}>
                            {doc.name}
                          </span>
                          {doc.alternatives?.length > 0 && (
                            <p className="text-xs text-navy-700/80 mt-1">
                              <span className="font-semibold text-leaf-800">Accepted Alternatives: </span>
                              {doc.alternatives.join(', ')}
                            </p>
                          )}
                        </div>
                      </div>

                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-ivory-100 text-navy-800 shrink-0">
                        Mandatory
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Official Submission Route */}
          {selectedScheme && (
            <Card className="p-6 space-y-3 bg-ivory-50/60 border border-ivory-200">
              <h4 className="font-bold text-sm text-navy-900 flex items-center gap-1.5">
                <ExternalLink className="w-4 h-4 text-leaf-700" />
                <span>Next: Official Government Submission</span>
              </h4>
              <p className="text-xs text-navy-700/80 leading-relaxed">
                JanSahayak does not charge processing fees or replace official government submissions. Once all checklist items are marked ready, submit your application at the official portal:
              </p>
              <div className="pt-1">
                <a
                  href={selectedScheme.official_portal_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-navy-900 text-white hover:bg-navy-800 text-xs font-semibold"
                >
                  <span>Open {selectedScheme.official_portal_url}</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </Card>
          )}

        </div>

      </div>

    </div>
  );
};
