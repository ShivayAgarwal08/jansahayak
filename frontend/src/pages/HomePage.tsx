import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import {
  Compass,
  Mic,
  Search,
  CheckCircle2,
  FileText,
  Shield,
  ArrowRight,
  Sprout,
  Home,
  HeartPulse,
  Users,
  ShieldCheck,
  Briefcase,
  GraduationCap,
  Sparkles,
  ExternalLink,
  Lock
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const { t, currentLanguage } = useLanguage();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [categories, setCategories] = useState<any[]>([]);
  const [schemes, setSchemes] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadHomeData = async () => {
      try {
        const [catsData, schemesData] = await Promise.all([
          api.getCategories(),
          api.getSchemes()
        ]);
        setCategories(catsData);
        setSchemes(schemesData.slice(0, 4));
      } catch (err) {
        console.error('Failed to load home data:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadHomeData();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/schemes?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      navigate('/schemes');
    }
  };

  const categoryIcons: Record<string, any> = {
    agriculture: Sprout,
    housing: Home,
    health: HeartPulse,
    women_children: Users,
    social_security: ShieldCheck,
    employment: Briefcase,
    education: GraduationCap,
  };

  return (
    <div className="space-y-16 sm:space-y-24 pb-20">
      
      {/* 1. Hero Section */}
      <section className="relative pt-10 sm:pt-16 pb-12 sm:pb-20 overflow-hidden">
        {/* Subtle decorative background pattern */}
        <div className="absolute inset-0 bg-gradient-to-b from-softmint/30 via-ivory-50 to-ivory-50 -z-10" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-softmint border border-leaf-200 text-leaf-800 text-xs sm:text-sm font-bold tracking-wide shadow-sm">
              <Sparkles className="w-4 h-4 text-leaf-700" />
              <span>{t('badge_verified')}</span>
            </div>

            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-navy-900 tracking-tight leading-[1.15]">
              {t('hero_title')}
            </h1>

            <p className="text-base sm:text-xl text-navy-800/80 leading-relaxed font-normal">
              {t('hero_subtitle')}
            </p>

            {/* Search & Voice Bar */}
            <form onSubmit={handleSearch} className="pt-2 max-w-2xl mx-auto">
              <div className="bg-white p-2 rounded-2xl shadow-civic-hover border border-ivory-200 flex flex-col sm:flex-row items-center gap-2">
                <div className="flex items-center gap-2 px-3 w-full">
                  <Search className="w-5 h-5 text-navy-700/50 shrink-0" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by scheme name, farmer, housing, health, pension..."
                    className="w-full py-2.5 text-sm sm:text-base bg-transparent text-navy-900 placeholder:text-navy-700/40 focus:outline-none"
                  />
                </div>
                <div className="flex items-center gap-2 w-full sm:w-auto shrink-0 justify-end">
                  <Link
                    to="/assistant"
                    className="p-3 rounded-xl bg-saffron-50 hover:bg-saffron-100 text-saffron-700 border border-saffron-200 transition-colors flex items-center justify-center gap-1.5 text-xs font-bold"
                    title="Ask with voice / आवाज़ से पूछें"
                  >
                    <Mic className="w-4 h-4 text-saffron-600 animate-pulse" />
                    <span className="hidden sm:inline">Voice</span>
                  </Link>
                  <Button type="submit" variant="primary" size="md" className="w-full sm:w-auto">
                    {t('cta_explore')}
                  </Button>
                </div>
              </div>
            </form>

            {/* Quick Filter Badges */}
            <div className="pt-2 flex flex-wrap items-center justify-center gap-2 text-xs text-navy-800/80">
              <span className="font-semibold text-navy-900">Popular:</span>
              <button
                type="button"
                onClick={() => navigate('/schemes?q=kisan')}
                className="px-3 py-1 rounded-full bg-white border border-ivory-200 hover:border-leaf-300 font-medium transition-colors"
              >
                PM-KISAN
              </button>
              <button
                type="button"
                onClick={() => navigate('/schemes?q=awaas')}
                className="px-3 py-1 rounded-full bg-white border border-ivory-200 hover:border-leaf-300 font-medium transition-colors"
              >
                PMAY-G Housing
              </button>
              <button
                type="button"
                onClick={() => navigate('/schemes?q=ayushman')}
                className="px-3 py-1 rounded-full bg-white border border-ivory-200 hover:border-leaf-300 font-medium transition-colors"
              >
                Ayushman Bharat (₹5 Lakh)
              </button>
              <button
                type="button"
                onClick={() => navigate('/schemes?q=pension')}
                className="px-3 py-1 rounded-full bg-white border border-ivory-200 hover:border-leaf-300 font-medium transition-colors"
              >
                Old Age Pension
              </button>
            </div>

          </div>

        </div>
      </section>

      {/* 2. Key Welfare Categories */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight">
              Explore by Welfare Category
            </h2>
            <p className="text-sm text-navy-700/70 mt-1">
              Central and state schemes verified directly from official gazettes and portals
            </p>
          </div>
          <Link
            to="/schemes"
            className="text-sm font-bold text-leaf-700 hover:text-leaf-800 flex items-center gap-1 group"
          >
            <span>View All</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
          {categories.map((cat) => {
            const Icon = categoryIcons[cat.id] || Compass;
            return (
              <Card
                key={cat.id}
                onClick={() => navigate(`/schemes?category=${cat.id}`)}
                className="p-5 cursor-pointer hover:border-leaf-500 hover:-translate-y-1 transition-all group"
              >
                <div className="w-12 h-12 rounded-2xl bg-leaf-50 group-hover:bg-leaf-700 group-hover:text-white transition-colors text-leaf-700 flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-base text-navy-900 group-hover:text-leaf-700 transition-colors">
                  {cat.name}
                </h3>
                <p className="text-xs text-navy-700/60 mt-1 font-medium">
                  {cat.count} Verified Scheme{cat.count !== 1 ? 's' : ''}
                </p>
              </Card>
            );
          })}
        </div>
      </section>

      {/* 3. Featured Verified Schemes */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight">
              Featured Verified Schemes
            </h2>
            <p className="text-sm text-navy-700/70 mt-1">
              Active welfare programs with full rule breakdowns and document checklists
            </p>
          </div>
          <Link
            to="/schemes"
            className="text-sm font-bold text-leaf-700 hover:text-leaf-800 flex items-center gap-1 group"
          >
            <span>Browse Directory</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {schemes.map((scheme) => (
            <Card key={scheme.id} className="p-6 flex flex-col justify-between hover:border-leaf-300">
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-leaf-700">
                      {scheme.department}
                    </span>
                    <h3 className="text-lg font-bold text-navy-900 mt-0.5">
                      {scheme.name}
                    </h3>
                    {scheme.name_hi && (
                      <p className="text-xs text-navy-700/70 font-medium">
                        {scheme.name_hi}
                      </p>
                    )}
                  </div>
                  <Badge variant="verified" size="sm">
                    Verified
                  </Badge>
                </div>

                <p className="text-sm text-navy-800/80 leading-relaxed line-clamp-2">
                  {scheme.summary}
                </p>

                <div className="p-3 rounded-xl bg-ivory-100/70 text-xs text-navy-900 space-y-1">
                  <span className="font-bold text-leaf-800">Key Benefit:</span>
                  <p className="leading-snug">{scheme.benefits_summary}</p>
                </div>
              </div>

              <div className="pt-6 border-t border-ivory-200 mt-6 flex items-center justify-between gap-3">
                <Link
                  to={`/eligibility?scheme=${scheme.slug}`}
                  className="text-xs font-bold text-leaf-700 hover:text-leaf-800 flex items-center gap-1"
                >
                  <span>Check Eligibility</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link
                  to={`/schemes/${scheme.slug}`}
                  className="px-3.5 py-2 rounded-xl bg-navy-900 hover:bg-navy-800 text-white text-xs font-semibold"
                >
                  View Details & Rules
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* 4. How JanSahayak Works */}
      <section className="bg-white py-16 sm:py-20 border-y border-ivory-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight">
              How JanSahayak Works For You
            </h2>
            <p className="text-sm sm:text-base text-navy-700/70 mt-2">
              Three simple steps from discovery to application without legal jargon or middlemen.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            <div className="space-y-4 text-center p-6 rounded-2xl bg-ivory-50 border border-ivory-200">
              <div className="w-14 h-14 rounded-2xl bg-leaf-100 text-leaf-700 flex items-center justify-center mx-auto text-xl font-extrabold">
                1
              </div>
              <h3 className="font-bold text-lg text-navy-900">
                1. Tell Us About Your Situation
              </h3>
              <p className="text-sm text-navy-700/80 leading-relaxed">
                Type or speak in your own language. Answer basic questions like state, age, and occupation—no sensitive Aadhaar numbers needed.
              </p>
            </div>

            <div className="space-y-4 text-center p-6 rounded-2xl bg-ivory-50 border border-ivory-200">
              <div className="w-14 h-14 rounded-2xl bg-saffron-100 text-saffron-700 flex items-center justify-center mx-auto text-xl font-extrabold">
                2
              </div>
              <h3 className="font-bold text-lg text-navy-900">
                2. Deterministic Qualification
              </h3>
              <p className="text-sm text-navy-700/80 leading-relaxed">
                Our Python rules engine evaluates verified scheme conditions transparently: see exactly which rules are met, missing, or disqualified.
              </p>
            </div>

            <div className="space-y-4 text-center p-6 rounded-2xl bg-ivory-50 border border-ivory-200">
              <div className="w-14 h-14 rounded-2xl bg-softsky text-blue-800 flex items-center justify-center mx-auto text-xl font-extrabold">
                3
              </div>
              <h3 className="font-bold text-lg text-navy-900">
                3. Prepare & Apply Officially
              </h3>
              <p className="text-sm text-navy-700/80 leading-relaxed">
                Review verified documents with accepted alternatives, download a printable CSC checklist PDF, and submit directly on the government portal.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* 5. Citizen Rights & Trust Charter */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl bg-navy-900 text-white p-8 sm:p-12 shadow-civic">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-navy-800 text-saffron-500 text-xs font-bold border border-navy-700">
                <Lock className="w-3.5 h-3.5" />
                <span>Our Privacy & Integrity Pledge</span>
              </div>
              <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
                Designed to Protect You, Not Harvest Your Data
              </h2>
              <p className="text-sm sm:text-base text-navy-200/80 leading-relaxed">
                We believe public welfare services must be completely trustworthy. JanSahayak does not collect Aadhaar numbers or bank passwords. We do not sell data or charge application fees.
              </p>
              <div className="pt-2 flex flex-wrap gap-4 text-xs font-semibold text-navy-200">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-leaf-500" />
                  <span>100% Free Public Service</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-leaf-500" />
                  <span>Verified Official Source Links</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-leaf-500" />
                  <span>Deterministic Non-Hallucinatory Rules</span>
                </div>
              </div>
            </div>

            <div className="bg-navy-800/80 rounded-2xl p-6 border border-navy-700 space-y-4">
              <h4 className="font-bold text-base text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-saffron-500" />
                <span>Facing Delays or Unjust Rejection?</span>
              </h4>
              <p className="text-xs sm:text-sm text-navy-200/80 leading-relaxed">
                Use our automated drafting assistants to prepare formal documents recognized under Indian administrative law:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <Link
                  to="/rti"
                  className="p-3 rounded-xl bg-navy-900 hover:bg-navy-950 border border-navy-700 text-xs font-bold text-white flex flex-col justify-between gap-1 transition-colors"
                >
                  <span className="text-saffron-500">Draft RTI Request</span>
                  <span className="text-[11px] font-normal text-navy-200/70">Seek official reasons for delay</span>
                </Link>
                <Link
                  to="/grievances"
                  className="p-3 rounded-xl bg-navy-900 hover:bg-navy-950 border border-navy-700 text-xs font-bold text-white flex flex-col justify-between gap-1 transition-colors"
                >
                  <span className="text-leaf-500">Public Grievance</span>
                  <span className="text-[11px] font-normal text-navy-200/70">Prepare CPGRAMS representation</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
};
