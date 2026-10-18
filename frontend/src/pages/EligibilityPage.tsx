import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import { Scheme, EligibilityResult } from '../types';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { useAuth } from '../context/AuthContext';
import {
  FileCheck2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Download,
  HelpCircle,
  ArrowRight,
  ShieldAlert,
  Building,
  RefreshCw
} from 'lucide-react';

export const EligibilityPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const schemeSlugFromUrl = searchParams.get('scheme') || 'pm-kisan';
  const { user } = useAuth();

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string>(schemeSlugFromUrl);
  const [isAssessing, setIsAssessing] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [result, setResult] = useState<EligibilityResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [profile, setProfile] = useState({
    age: 42,
    gender: 'female',
    state: user?.state || 'Uttar Pradesh',
    occupation: 'farmer',
    owns_cultivable_land: true,
    landholding_acres: 2.0,
    housing_type: 'kutcha',
    area_type: 'rural',
    is_bpl: true,
    is_govt_employee: false,
    pays_income_tax: false,
    is_pregnant_or_lactating: false,
    has_girl_child_under_10: false,
    girl_child_age: 5,
    is_street_vendor: false,
    is_traditional_artisan: false,
  });

  useEffect(() => {
    const loadSchemes = async () => {
      try {
        const scs = await api.getSchemes();
        setSchemes(scs);
      } catch (err) {
        console.error('Error fetching schemes for eligibility:', err);
      }
    };
    loadSchemes();
  }, []);

  useEffect(() => {
    if (schemeSlugFromUrl && schemeSlugFromUrl !== selectedSlug) {
      setSelectedSlug(schemeSlugFromUrl);
    }
  }, [schemeSlugFromUrl]);

  const handleSchemeChange = (slug: string) => {
    setSelectedSlug(slug);
    setSearchParams({ scheme: slug });
    setResult(null);
  };

  const handleAssess = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAssessing(true);
    setError(null);
    try {
      const data = await api.assessEligibility(selectedSlug, profile);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to complete eligibility assessment.');
    } finally {
      setIsAssessing(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!result) return;
    setIsDownloading(true);
    try {
      const blob = await api.downloadReportPdf(selectedSlug, profile);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `JanSahayak_Report_${selectedSlug}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert('Error downloading report: ' + err.message);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-softmint text-leaf-800 text-xs font-bold border border-leaf-200">
          <FileCheck2 className="w-3.5 h-3.5" />
          <span>Deterministic Qualification Engine</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-900 tracking-tight">
          Check Scheme Eligibility
        </h1>
        <p className="text-sm sm:text-base text-navy-700/80">
          Evaluated against official government gazettes using strict rules without AI hallucinations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Form: Citizen Input (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="p-6">
            <form onSubmit={handleAssess} className="space-y-4">
              
              {/* Scheme Selector */}
              <div>
                <label className="block text-xs font-bold uppercase text-navy-900 mb-1.5">
                  Select Government Scheme
                </label>
                <select
                  value={selectedSlug}
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

              {/* Age & Gender */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-navy-800 mb-1">
                    Applicant Age
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="110"
                    value={profile.age}
                    onChange={(e) => setProfile({ ...profile, age: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-navy-800 mb-1">
                    Gender
                  </label>
                  <select
                    value={profile.gender}
                    onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                  >
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              {/* State */}
              <div>
                <label className="block text-xs font-bold text-navy-800 mb-1">
                  State of Residence
                </label>
                <input
                  type="text"
                  value={profile.state}
                  onChange={(e) => setProfile({ ...profile, state: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                  placeholder="e.g. Uttar Pradesh, Bihar, Rajasthan"
                />
              </div>

              {/* Occupation & Land */}
              <div>
                <label className="block text-xs font-bold text-navy-800 mb-1">
                  Primary Occupation
                </label>
                <select
                  value={profile.occupation}
                  onChange={(e) => setProfile({ ...profile, occupation: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none"
                >
                  <option value="farmer">Farmer / Agricultural Worker</option>
                  <option value="street_vendor">Street Vendor / Hawker</option>
                  <option value="artisan">Artisan / Craftsperson (Carpenter, Mason, etc.)</option>
                  <option value="daily_wage">Daily Wage Labourer</option>
                  <option value="salaried">Private Salaried / Employee</option>
                  <option value="homemaker">Homemaker / Mother</option>
                  <option value="retired">Senior Citizen / Retired</option>
                  <option value="student">Student</option>
                </select>
              </div>

              {/* Conditional: Landholding for Farmers */}
              {selectedSlug === 'pm-kisan' && (
                <div className="p-3.5 rounded-xl bg-ivory-50 border border-ivory-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-navy-900">Owns Cultivable Land?</span>
                    <input
                      type="checkbox"
                      checked={profile.owns_cultivable_land}
                      onChange={(e) => setProfile({ ...profile, owns_cultivable_land: e.target.checked })}
                      className="w-4 h-4 text-leaf-700 rounded"
                    />
                  </div>
                  {profile.owns_cultivable_land && (
                    <div>
                      <label className="block text-[11px] font-semibold text-navy-700 mb-1">
                        Land Area (Acres)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={profile.landholding_acres}
                        onChange={(e) => setProfile({ ...profile, landholding_acres: parseFloat(e.target.value) || 0 })}
                        className="w-full px-2.5 py-1.5 rounded-lg border border-ivory-300 text-xs"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Housing Condition for PMAY */}
              {selectedSlug === 'pmay-g' && (
                <div className="p-3.5 rounded-xl bg-ivory-50 border border-ivory-200 space-y-3">
                  <label className="block text-xs font-bold text-navy-900">
                    Current Dwelling Status
                  </label>
                  <select
                    value={profile.housing_type}
                    onChange={(e) => setProfile({ ...profile, housing_type: e.target.value })}
                    className="w-full px-2.5 py-2 rounded-lg border border-ivory-300 text-xs"
                  >
                    <option value="kutcha">Living in Kutcha / Dilapidated House</option>
                    <option value="houseless">Houseless / No Land Rights</option>
                    <option value="pucca">Already Own a Pucca House</option>
                  </select>
                </div>
              )}

              {/* Sukanya girl child conditional */}
              {selectedSlug === 'sukanya-samriddhi-yojana' && (
                <div className="p-3.5 rounded-xl bg-ivory-50 border border-ivory-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-navy-900">Girl child under 10 years?</span>
                    <input
                      type="checkbox"
                      checked={profile.has_girl_child_under_10}
                      onChange={(e) => setProfile({ ...profile, has_girl_child_under_10: e.target.checked })}
                      className="w-4 h-4 text-leaf-700 rounded"
                    />
                  </div>
                  {profile.has_girl_child_under_10 && (
                    <div>
                      <label className="block text-[11px] font-semibold text-navy-700 mb-1">
                        Girl Child's Age (Years)
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="10"
                        value={profile.girl_child_age}
                        onChange={(e) => setProfile({ ...profile, girl_child_age: parseInt(e.target.value) || 0 })}
                        className="w-full px-2.5 py-1.5 rounded-lg border border-ivory-300 text-xs"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Statutory Exclusions Checkboxes */}
              <div className="pt-2 border-t border-ivory-200 space-y-2 text-xs">
                <span className="font-bold text-navy-900 block text-[11px] uppercase tracking-wider text-navy-700/80">
                  Statutory Disqualification Checks
                </span>
                
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.is_bpl}
                    onChange={(e) => setProfile({ ...profile, is_bpl: e.target.checked })}
                    className="w-4 h-4 text-leaf-700 rounded"
                  />
                  <span>Belongs to BPL / Deprived List</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.is_govt_employee}
                    onChange={(e) => setProfile({ ...profile, is_govt_employee: e.target.checked })}
                    className="w-4 h-4 text-red-600 rounded"
                  />
                  <span>Any family member is regular Govt/PSU employee</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={profile.pays_income_tax}
                    onChange={(e) => setProfile({ ...profile, pays_income_tax: e.target.checked })}
                    className="w-4 h-4 text-red-600 rounded"
                  />
                  <span>Paid Income Tax in last assessment year</span>
                </label>
              </div>

              <div className="pt-3">
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  isLoading={isAssessing}
                  className="w-full"
                >
                  Run Qualification Assessment
                </Button>
              </div>

            </form>
          </Card>
        </div>

        {/* Right Output: Deterministic Results (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {error && (
            <Alert type="error" title="Assessment Failed">
              {error}
            </Alert>
          )}

          {!result && !error && (
            <Card className="p-10 text-center space-y-4 bg-white/70 border-dashed border-2 border-ivory-300">
              <div className="w-14 h-14 rounded-full bg-softmint text-leaf-700 flex items-center justify-center mx-auto">
                <FileCheck2 className="w-7 h-7" />
              </div>
              <h3 className="font-bold text-lg text-navy-900">
                Ready to Evaluate
              </h3>
              <p className="text-sm text-navy-700/70 max-w-md mx-auto">
                Fill in your general citizen profile on the left and click 'Run Qualification Assessment' to see the transparent rule-by-rule breakdown.
              </p>
            </Card>
          )}

          {result && (
            <div className="space-y-6">
              
              {/* Status Header Banner */}
              <div
                className={`p-6 rounded-2xl border ${
                  result.status === 'eligible'
                    ? 'bg-softmint border-leaf-300'
                    : result.status === 'possibly_eligible'
                    ? 'bg-amber-50 border-amber-300'
                    : 'bg-red-50 border-red-300'
                } space-y-3`}
              >
                <div className="flex items-center justify-between gap-3">
                  <Badge variant={result.status} size="md">
                    {result.status === 'eligible'
                      ? 'Appears Eligible'
                      : result.status === 'possibly_eligible'
                      ? 'Possibly Eligible (More Info Needed)'
                      : 'Appears Ineligible Under Verified Rules'}
                  </Badge>
                  <span className="text-xs text-navy-700/70 font-semibold">
                    {new Date(result.assessed_at).toLocaleDateString()}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-navy-950">
                  {result.scheme_name}
                </h3>

                <p className="text-sm text-navy-900/90 leading-relaxed font-medium">
                  {result.summary_explanation}
                </p>

                <div className="pt-2 flex flex-wrap items-center gap-3">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleDownloadReport}
                    isLoading={isDownloading}
                    leftIcon={<Download className="w-4 h-4" />}
                  >
                    Download Citizen Report PDF
                  </Button>
                  <Link to={`/applications?scheme=${result.scheme_slug}`}>
                    <Button variant="outline" size="sm">
                      Prepare Application
                    </Button>
                  </Link>
                </div>
              </div>

              {/* Conditions Satisfied */}
              {result.satisfied_conditions.length > 0 && (
                <Card className="p-6 space-y-3">
                  <h4 className="text-sm font-bold uppercase tracking-wider text-leaf-800 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-leaf-700" />
                    <span>Satisfied Criteria ({result.satisfied_conditions.length})</span>
                  </h4>
                  <div className="space-y-2">
                    {result.satisfied_conditions.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-ivory-50 border border-ivory-200 text-xs space-y-0.5">
                        <div className="flex items-center justify-between font-bold text-navy-900">
                          <span>{item.criterion}</span>
                          <span className="text-leaf-700 font-semibold">{String(item.citizen_value)}</span>
                        </div>
                        {item.official_rule && (
                          <p className="text-navy-700/70 text-[11px]">
                            <b>Rule:</b> {item.official_rule}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Conditions Unsatisfied */}
              {result.unsatisfied_conditions.length > 0 && (
                <Card className="p-6 space-y-3 border-red-200 bg-red-50/20">
                  <h4 className="text-sm font-bold uppercase tracking-wider text-red-800 flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-red-600" />
                    <span>Unsatisfied Disqualifications ({result.unsatisfied_conditions.length})</span>
                  </h4>
                  <div className="space-y-2">
                    {result.unsatisfied_conditions.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-white border border-red-200 text-xs space-y-1">
                        <div className="flex items-center justify-between font-bold text-red-950">
                          <span>{item.criterion}</span>
                          <span className="text-red-700 font-semibold">{String(item.citizen_value)}</span>
                        </div>
                        <p className="text-red-900/90 text-xs font-medium">
                          {item.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Unknown / Missing */}
              {result.unknown_conditions.length > 0 && (
                <Card className="p-6 space-y-3 border-amber-200 bg-amber-50/20">
                  <h4 className="text-sm font-bold uppercase tracking-wider text-amber-900 flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-amber-600" />
                    <span>Missing Details Requiring Confirmation ({result.unknown_conditions.length})</span>
                  </h4>
                  <div className="space-y-2">
                    {result.unknown_conditions.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-white border border-amber-200 text-xs space-y-0.5">
                        <span className="font-bold text-amber-950">{item.criterion}:</span>
                        <p className="text-navy-800">{item.prompt}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Actionable Next Steps */}
              <Card className="p-6 space-y-3">
                <h4 className="text-sm font-bold uppercase tracking-wider text-navy-900 flex items-center gap-2">
                  <ArrowRight className="w-4 h-4 text-leaf-700" />
                  <span>Recommended Actionable Next Steps</span>
                </h4>
                <ol className="space-y-2 text-xs text-navy-800">
                  {result.next_steps.map((step, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="font-bold text-leaf-700">•</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              </Card>

              {/* Official Disclaimer */}
              <div className="p-4 rounded-xl bg-ivory-100 text-xs text-navy-700/80 leading-relaxed italic border border-ivory-200">
                {result.disclaimer}
              </div>

            </div>
          )}

        </div>

      </div>

    </div>
  );
};
