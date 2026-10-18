import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Scheme } from '../types';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck,
  ExternalLink,
  FileCheck,
  AlertTriangle,
  FileText,
  Bookmark,
  Share2,
  Calendar,
  Building2,
  ListOrdered,
  ArrowLeft
} from 'lucide-react';

export const SchemeDetailPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchDetail = async () => {
      if (!slug) return;
      setIsLoading(true);
      try {
        const data = await api.getScheme(slug);
        setScheme(data);
      } catch (err: any) {
        setError(err.message || 'Scheme not found');
      } finally {
        setIsLoading(false);
      }
    };
    fetchDetail();
  }, [slug]);

  const handleSaveToggle = async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    if (!scheme) return;
    try {
      const res = await api.toggleSaveScheme(scheme.id);
      setIsSaved(res.saved);
      setSaveMessage(res.message);
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-leaf-700 border-t-transparent rounded-full mx-auto" />
        <p className="text-sm text-navy-700/70 mt-4">Loading verified government scheme details...</p>
      </div>
    );
  }

  if (error || !scheme) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 space-y-4">
        <Alert type="error" title="Scheme Not Found">
          {error || 'Unable to load scheme details.'}
        </Alert>
        <Link to="/schemes">
          <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
            Back to Scheme Directory
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Back button */}
      <div>
        <Link
          to="/schemes"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-navy-700 hover:text-leaf-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Scheme Directory</span>
        </Link>
      </div>

      {/* Main Header Card */}
      <Card className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-leaf-700">
                {scheme.department}
              </span>
              <span className="text-ivory-300">•</span>
              <span className="text-xs font-semibold text-navy-700">
                {scheme.scope.toUpperCase()} SCHEME
              </span>
              <Badge variant="verified" size="sm">
                Verified Official
              </Badge>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight">
              {scheme.name}
            </h1>
            {scheme.name_hi && (
              <p className="text-base font-semibold text-navy-700/80">
                {scheme.name_hi}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveToggle}
              leftIcon={<Bookmark className={`w-4 h-4 ${isSaved ? 'fill-leaf-700 text-leaf-700' : ''}`} />}
            >
              {isSaved ? 'Saved' : 'Save Scheme'}
            </Button>
          </div>
        </div>

        {saveMessage && (
          <Alert type="success">{saveMessage}</Alert>
        )}

        <p className="text-base text-navy-800/90 leading-relaxed font-normal">
          {scheme.summary}
        </p>

        {/* Benefits Highlight Box */}
        <div className="p-4 sm:p-5 rounded-xl bg-softmint border border-leaf-200 space-y-1.5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-leaf-800 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-leaf-700" />
            <span>Official Benefits & Entitlements</span>
          </h4>
          <p className="text-sm font-semibold text-leaf-950 leading-relaxed">
            {scheme.benefits_summary}
          </p>
        </div>

        {/* Action CTAs */}
        <div className="pt-4 flex flex-wrap items-center gap-3 border-t border-ivory-200">
          <Link to={`/eligibility?scheme=${scheme.slug}`}>
            <Button variant="primary" size="md">
              Evaluate My Eligibility
            </Button>
          </Link>
          <a
            href={scheme.official_portal_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-ivory-300 hover:bg-ivory-100 text-sm font-semibold text-navy-900 transition-colors"
          >
            <span>Official Application Portal</span>
            <ExternalLink className="w-4 h-4 text-navy-700/60" />
          </a>
        </div>
      </Card>

      {/* Grid of Rules and Documents */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Left: Eligibility & Exclusions */}
        <div className="space-y-6">
          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-bold text-navy-900 flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-leaf-700" />
              <span>Eligibility Conditions</span>
            </h3>
            <p className="text-xs text-navy-700/70">
              Evaluated strictly through JanSahayak's deterministic Python rules engine.
            </p>
            <div className="space-y-2 text-sm text-navy-800">
              {Object.entries(scheme.eligibility_rules || {}).map(([key, val]) => (
                <div key={key} className="p-2.5 rounded-lg bg-ivory-50 border border-ivory-200 flex justify-between gap-2">
                  <span className="font-semibold text-xs text-navy-900 uppercase">
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <span className="text-xs font-medium text-navy-700 text-right">
                    {Array.isArray(val) ? val.join(', ') : String(val)}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-bold text-navy-900 flex items-center gap-2 text-red-900">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span>Official Exclusions</span>
            </h3>
            <p className="text-xs text-navy-700/70">
              The following categories are disqualified under official government notifications:
            </p>
            <ul className="space-y-2 text-xs text-navy-800">
              {scheme.exclusions?.map((exc, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-red-500 font-bold">•</span>
                  <span>{exc}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>

        {/* Right: Required Documents & Application Steps */}
        <div className="space-y-6">
          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-bold text-navy-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-saffron-600" />
              <span>Required Documents Checklist</span>
            </h3>
            <div className="space-y-3">
              {scheme.required_documents?.map((doc, idx) => (
                <div key={idx} className="p-3 rounded-xl border border-ivory-200 bg-ivory-50/50 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-navy-900">{doc.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-leaf-100 text-leaf-800">
                      Mandatory
                    </span>
                  </div>
                  {doc.alternatives?.length > 0 && (
                    <p className="text-[11px] text-navy-700/70">
                      <b>Accepted Alternatives:</b> {doc.alternatives.join(', ')}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-bold text-navy-900 flex items-center gap-2">
              <ListOrdered className="w-5 h-5 text-navy-700" />
              <span>Step-by-Step Application Guide</span>
            </h3>
            <ol className="space-y-3 text-xs text-navy-800">
              {scheme.application_steps?.map((step, idx) => (
                <li key={idx} className="flex items-start gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-navy-900 text-white flex items-center justify-center shrink-0 font-bold text-[10px]">
                    {idx + 1}
                  </span>
                  <span className="leading-relaxed">{step}</span>
                </li>
              ))}
            </ol>
          </Card>
        </div>

      </div>

      {/* Official Government Sources & Provenance */}
      <Card className="p-6 space-y-4 bg-white border border-ivory-200">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-navy-900 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-leaf-700" />
            <span>Official Government Sources & Verification Provenance</span>
          </h3>
          <span className="text-xs text-navy-700/60 font-medium">
            Last Verified: {new Date(scheme.last_verified_at).toLocaleDateString()}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {scheme.sources?.map((src) => (
            <div key={src.id} className="p-3.5 rounded-xl bg-ivory-50 border border-ivory-200 space-y-1.5">
              <div className="flex items-start justify-between gap-2">
                <span className="text-xs font-bold text-navy-900">{src.source_title}</span>
                <a
                  href={src.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-leaf-700 hover:text-leaf-800"
                  title="Open official document"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
              <p className="text-[11px] text-navy-700/70">
                <b>Issuing Authority:</b> {src.issuing_authority}
              </p>
              {src.document_reference && (
                <p className="text-[11px] text-navy-700/70">
                  <b>Ref:</b> {src.document_reference}
                </p>
              )}
            </div>
          ))}
        </div>
      </Card>

    </div>
  );
};
