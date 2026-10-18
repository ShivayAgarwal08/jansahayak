import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Scheme } from '../types';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Search, Filter, ArrowRight, CheckSquare, Square, Layers, RefreshCw } from 'lucide-react';

const INDIAN_STATES = [
  'ALL',
  'Andhra Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Delhi',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Tamil Nadu',
  'Telangana',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal'
];

export const SchemesPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters from URL
  const selectedCategory = searchParams.get('category') || 'all';
  const selectedState = searchParams.get('state') || 'ALL';
  const searchQuery = searchParams.get('q') || '';
  const [selectedSlugsForCompare, setSelectedSlugsForCompare] = useState<string[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [cats, scs] = await Promise.all([
          api.getCategories(),
          api.getSchemes({
            category: selectedCategory,
            state: selectedState,
            q: searchQuery
          })
        ]);
        setCategories(cats);
        setSchemes(scs);
      } catch (err) {
        console.error('Error fetching schemes:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [selectedCategory, selectedState, searchQuery]);

  const updateFilter = (key: string, val: string) => {
    const current = new URLSearchParams(searchParams);
    if (val && val !== 'all' && val !== 'ALL') {
      current.set(key, val);
    } else {
      current.delete(key);
    }
    setSearchParams(current);
  };

  const toggleCompare = (slug: string) => {
    if (selectedSlugsForCompare.includes(slug)) {
      setSelectedSlugsForCompare(selectedSlugsForCompare.filter((s) => s !== slug));
    } else {
      if (selectedSlugsForCompare.length >= 4) {
        alert('You can compare a maximum of 4 schemes at once.');
        return;
      }
      setSelectedSlugsForCompare([...selectedSlugsForCompare, slug]);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-navy-900 tracking-tight">
          Government Welfare Schemes Catalogue
        </h1>
        <p className="text-sm sm:text-base text-navy-700/80">
          Verified central and state government welfare schemes with deterministic eligibility criteria and authentic source portals.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-white border border-ivory-200 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          
          {/* Keyword Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-navy-700/50 absolute left-3 top-3.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => updateFilter('q', e.target.value)}
              placeholder="Search by scheme name or keywords..."
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-ivory-200 text-sm focus:outline-none focus:border-leaf-600 bg-ivory-50/50"
            />
          </div>

          {/* Category Dropdown */}
          <div className="relative">
            <select
              value={selectedCategory}
              onChange={(e) => updateFilter('category', e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-ivory-200 text-sm focus:outline-none focus:border-leaf-600 bg-ivory-50/50 text-navy-900 font-medium"
            >
              <option value="all">All Welfare Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.count})
                </option>
              ))}
            </select>
          </div>

          {/* State Dropdown */}
          <div className="relative">
            <select
              value={selectedState}
              onChange={(e) => updateFilter('state', e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-ivory-200 text-sm focus:outline-none focus:border-leaf-600 bg-ivory-50/50 text-navy-900 font-medium"
            >
              {INDIAN_STATES.map((st) => (
                <option key={st} value={st}>
                  {st === 'ALL' ? 'All India (Central & All States)' : st}
                </option>
              ))}
            </select>
          </div>

        </div>

        {/* Results summary and reset */}
        <div className="flex items-center justify-between text-xs text-navy-700/70 pt-2 border-t border-ivory-100">
          <span>
            Found <b>{schemes.length}</b> verified scheme{schemes.length !== 1 ? 's' : ''}
          </span>
          {(selectedCategory !== 'all' || selectedState !== 'ALL' || searchQuery) && (
            <button
              onClick={() => setSearchParams({})}
              className="flex items-center gap-1 text-leaf-700 hover:text-leaf-800 font-bold"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset Filters</span>
            </button>
          )}
        </div>
      </div>

      {/* Schemes Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-64 rounded-2xl bg-ivory-200/50" />
          ))}
        </div>
      ) : schemes.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white border border-ivory-200 space-y-3">
          <p className="text-base font-bold text-navy-900">No schemes found matching your criteria.</p>
          <p className="text-xs text-navy-700/70">
            Try resetting your search query or selecting 'All Welfare Categories'.
          </p>
          <Button variant="outline" size="sm" onClick={() => setSearchParams({})}>
            View All Schemes
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {schemes.map((scheme) => {
            const isComparing = selectedSlugsForCompare.includes(scheme.slug);
            return (
              <Card key={scheme.id} className="p-6 flex flex-col justify-between hover:border-leaf-300">
                <div className="space-y-4">
                  
                  {/* Top Bar: Dept & Comparison Toggle */}
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
                    <button
                      type="button"
                      onClick={() => toggleCompare(scheme.slug)}
                      className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition-colors ${
                        isComparing
                          ? 'bg-leaf-700 text-white border-leaf-700 font-bold'
                          : 'border-ivory-300 text-navy-700 hover:bg-ivory-100'
                      }`}
                      title="Compare side-by-side"
                    >
                      {isComparing ? (
                        <>
                          <CheckSquare className="w-3.5 h-3.5" />
                          <span>Comparing</span>
                        </>
                      ) : (
                        <>
                          <Square className="w-3.5 h-3.5" />
                          <span>Compare</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Summary */}
                  <p className="text-sm text-navy-800/80 leading-relaxed line-clamp-3">
                    {scheme.summary}
                  </p>

                  {/* Key Benefits */}
                  <div className="p-3 rounded-xl bg-ivory-100/70 text-xs text-navy-900 space-y-1">
                    <span className="font-bold text-leaf-800">Key Benefit:</span>
                    <p className="leading-snug">{scheme.benefits_summary}</p>
                  </div>

                  {/* Target Beneficiaries Tags */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {scheme.beneficiary_types?.map((b) => (
                      <span
                        key={b}
                        className="text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-ivory-100 text-navy-800"
                      >
                        {b.replace(/_/g, ' ').toUpperCase()}
                      </span>
                    ))}
                    <Badge variant="verified" size="sm">
                      Verified
                    </Badge>
                  </div>
                </div>

                {/* Bottom Action CTAs */}
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
            );
          })}
        </div>
      )}

      {/* Sticky Bottom Comparison Floating Bar */}
      {selectedSlugsForCompare.length >= 2 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 bg-navy-900 text-white px-6 py-3.5 rounded-2xl shadow-civic-hover border border-navy-700 flex items-center gap-4">
          <Layers className="w-5 h-5 text-saffron-500" />
          <div className="text-sm font-semibold">
            {selectedSlugsForCompare.length} Schemes Selected for Comparison
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(`/compare?slugs=${selectedSlugsForCompare.join(',')}`)}
          >
            Compare Now
          </Button>
          <button
            onClick={() => setSelectedSlugsForCompare([])}
            className="text-xs text-navy-300 hover:text-white underline ml-2"
          >
            Clear
          </button>
        </div>
      )}

    </div>
  );
};
