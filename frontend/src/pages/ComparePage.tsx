import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Scheme } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Alert } from '../components/common/Alert';
import { Layers, ArrowLeft, ExternalLink, ShieldCheck, CheckCircle } from 'lucide-react';

export const ComparePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const slugsParam = searchParams.get('slugs') || 'pm-kisan,pmay-g';

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchComparison = async () => {
      const slugs = slugsParam.split(',').filter(Boolean);
      if (slugs.length < 2) {
        setError('Please select at least 2 schemes to compare.');
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      try {
        const data = await api.compareSchemes(slugs);
        setSchemes(data);
      } catch (err: any) {
        setError(err.message || 'Error loading scheme comparison.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchComparison();
  }, [slugsParam]);

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-leaf-700 border-t-transparent rounded-full mx-auto" />
        <p className="text-sm text-navy-700/70 mt-3 font-medium">Comparing verified scheme criteria...</p>
      </div>
    );
  }

  if (error || schemes.length < 2) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 space-y-4">
        <Alert type="warning" title="Comparison Not Available">
          {error || 'Please select 2 to 4 schemes from the catalogue.'}
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-softsky text-blue-900 text-xs font-bold border border-blue-200">
            <Layers className="w-3.5 h-3.5" />
            <span>Side-by-Side Scheme Comparison</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight">
            Compare Government Welfare Programs
          </h1>
        </div>

        <Link to="/schemes">
          <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
            Back to Directory
          </Button>
        </Link>
      </div>

      {/* Comparison Table / Grid */}
      <div className="overflow-x-auto pb-4">
        <div
          className="grid gap-4 min-w-[700px]"
          style={{ gridTemplateColumns: `repeat(${schemes.length}, minmax(300px, 1fr))` }}
        >
          {schemes.map((scheme) => (
            <Card key={scheme.id} className="p-6 flex flex-col justify-between space-y-6 bg-white">
              <div className="space-y-4">
                
                {/* Header */}
                <div>
                  <span className="text-[11px] font-bold uppercase text-leaf-700 tracking-wider">
                    {scheme.department}
                  </span>
                  <h3 className="text-lg font-bold text-navy-900 mt-1">
                    {scheme.name}
                  </h3>
                  {scheme.name_hi && (
                    <p className="text-xs text-navy-700/80 font-medium">{scheme.name_hi}</p>
                  )}
                  <div className="pt-2">
                    <Badge variant="verified" size="sm">
                      Official Verified
                    </Badge>
                  </div>
                </div>

                {/* Key Benefits */}
                <div className="p-3.5 rounded-xl bg-softmint border border-leaf-200 text-xs space-y-1">
                  <span className="font-bold text-leaf-900 uppercase tracking-wide text-[10px]">
                    Financial & Welfare Benefits:
                  </span>
                  <p className="text-leaf-950 leading-relaxed font-semibold">
                    {scheme.benefits_summary}
                  </p>
                </div>

                {/* Target Beneficiaries */}
                <div className="space-y-1.5 text-xs">
                  <span className="font-bold text-navy-900 text-[11px] uppercase tracking-wide">
                    Target Beneficiaries:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {scheme.beneficiary_types?.map((b) => (
                      <span key={b} className="px-2 py-0.5 rounded bg-ivory-100 text-navy-800 text-[10px] font-semibold">
                        {b.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Eligibility Criteria */}
                <div className="space-y-1.5 text-xs pt-2 border-t border-ivory-200">
                  <span className="font-bold text-navy-900 text-[11px] uppercase tracking-wide">
                    Core Eligibility Rules:
                  </span>
                  <div className="space-y-1 text-navy-800 text-[11px]">
                    {Object.entries(scheme.eligibility_rules || {}).map(([k, v]) => (
                      <div key={k} className="p-1.5 rounded bg-ivory-50 flex justify-between">
                        <span className="capitalize">{k.replace(/_/g, ' ')}:</span>
                        <span className="font-semibold">{Array.isArray(v) ? v.join(', ') : String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Required Documents */}
                <div className="space-y-1.5 text-xs pt-2 border-t border-ivory-200">
                  <span className="font-bold text-navy-900 text-[11px] uppercase tracking-wide">
                    Required Documents:
                  </span>
                  <ul className="space-y-1 text-navy-800 text-[11px]">
                    {scheme.required_documents?.map((d, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <CheckCircle className="w-3.5 h-3.5 text-leaf-700 shrink-0 mt-0.5" />
                        <span>{d.name}</span>
                      </li>
                    ))}
                  </ul>
                </div>

              </div>

              {/* CTAs */}
              <div className="pt-4 border-t border-ivory-200 space-y-2">
                <Link to={`/eligibility?scheme=${scheme.slug}`} className="block">
                  <Button variant="primary" size="sm" className="w-full">
                    Check My Eligibility
                  </Button>
                </Link>
                <a
                  href={scheme.official_portal_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full text-center block px-3 py-2 rounded-xl border border-ivory-300 text-xs font-semibold text-navy-900 hover:bg-ivory-100"
                >
                  Official Portal
                </a>
              </div>
            </Card>
          ))}
        </div>
      </div>

    </div>
  );
};
