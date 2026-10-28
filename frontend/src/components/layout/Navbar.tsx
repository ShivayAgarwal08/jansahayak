import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLanguage, LANGUAGES } from '../../context/LanguageContext';
import {
  Home,
  Compass,
  Mic,
  FileText,
  FileCheck2,
  AlertCircle,
  Scale,
  ChevronDown,
  User as UserIcon,
  Globe,
  Menu,
  X,
  LogOut,
  ShieldCheck
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const { currentLanguage, setLanguage, t } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const location = useLocation();

  const langRef = useRef<HTMLDivElement>(null);
  const moreRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (langRef.current && !langRef.current.contains(event.target as Node)) {
        setLangMenuOpen(false);
      }
      if (moreRef.current && !moreRef.current.contains(event.target as Node)) {
        setMoreMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Primary navigation items requested in Phase 2
  const primaryNavLinks = [
    { to: '/', label: t('nav_home') || 'Home', icon: Home },
    { to: '/schemes', label: t('nav_find_schemes') || 'Find Schemes', icon: Compass },
    { to: '/assistant', label: t('nav_ai_assistant') || 'AI Assistant', icon: Mic },
    { to: '/applications', label: t('nav_applications') || 'My Applications', icon: FileText },
  ];

  // Secondary utilities moved into "More Services" dropdown
  const secondaryNavLinks = [
    { to: '/eligibility', label: t('nav_eligibility') || 'Eligibility Calculator', icon: FileCheck2 },
    { to: '/compare', label: t('nav_compare') || 'Compare Schemes', icon: Scale },
    { to: '/rti', label: t('nav_rti') || 'RTI Drafter (Sec 6(1))', icon: FileText },
    { to: '/grievances', label: t('nav_grievance') || 'Public Grievance (CPGRAMS)', icon: AlertCircle },
  ];

  const currentLangObj = LANGUAGES.find((l) => l.code === currentLanguage) || LANGUAGES[0];
  const isActive = (path: string) => location.pathname === path;
  const isSecondaryActive = secondaryNavLinks.some((l) => location.pathname === l.to);

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-ivory-200">
      {/* Discreet Platform Identity Banner */}
      <div className="bg-ivory-100/80 border-b border-ivory-200 text-center py-1 px-4 text-[11px] text-navy-700/80">
        <span className="font-semibold text-leaf-800">JanSahayak</span> — Independent Civic AI Assistance Platform • Not an Official Government Agency
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-navy-900 flex items-center justify-center text-white shadow-sm group-hover:bg-leaf-700 transition-colors">
              <span className="font-extrabold text-lg tracking-tight text-saffron-500">जन</span>
            </div>
            <div>
              <span className="text-xl sm:text-2xl font-extrabold tracking-tight text-navy-900 flex items-center gap-1.5">
                JanSahayak
                <span className="text-xs px-2 py-0.5 rounded-full bg-softmint text-leaf-800 font-semibold border border-leaf-200 hidden sm:inline-block">
                  Civic AI
                </span>
              </span>
              <p className="text-[11px] font-medium text-navy-700/70 -mt-0.5 hidden sm:block">
                नागरिक कल्याण सेवा पोर्टल
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-1" aria-label="Main Navigation">
            {primaryNavLinks.map((link) => {
              const Icon = link.icon;
              const active = isActive(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors ${
                    active
                      ? 'bg-leaf-50 text-leaf-800 border border-leaf-200/80 shadow-xs'
                      : 'text-navy-900/80 hover:text-navy-900 hover:bg-ivory-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-leaf-700' : 'text-navy-700/60'}`} />
                  {link.label}
                </Link>
              );
            })}

            {/* Compact "More Services" Dropdown */}
            <div className="relative" ref={moreRef}>
              <button
                type="button"
                onClick={() => setMoreMenuOpen(!moreMenuOpen)}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors ${
                  isSecondaryActive
                    ? 'bg-leaf-50 text-leaf-800 border border-leaf-200/80'
                    : 'text-navy-900/80 hover:text-navy-900 hover:bg-ivory-100'
                }`}
                aria-expanded={moreMenuOpen}
                aria-haspopup="true"
              >
                <span>{t('nav_more_services') || 'More Services'}</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${moreMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {moreMenuOpen && (
                <div className="absolute left-0 mt-2 w-64 bg-white rounded-xl shadow-civic-hover border border-ivory-200 py-1.5 z-50">
                  <div className="px-3 py-1 text-[11px] font-bold text-navy-700/60 uppercase tracking-wider">
                    Secondary Civic Tools
                  </div>
                  {secondaryNavLinks.map((sublink) => {
                    const SubIcon = sublink.icon;
                    const subActive = isActive(sublink.to);
                    return (
                      <Link
                        key={sublink.to}
                        to={sublink.to}
                        onClick={() => setMoreMenuOpen(false)}
                        className={`flex items-center gap-2.5 px-3.5 py-2.5 text-sm transition-colors ${
                          subActive
                            ? 'bg-leaf-50 text-leaf-800 font-bold'
                            : 'text-navy-900 hover:bg-ivory-100'
                        }`}
                      >
                        <SubIcon className={`w-4 h-4 ${subActive ? 'text-leaf-700' : 'text-navy-700/60'}`} />
                        <span>{sublink.label}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          </nav>

          {/* Right Action Items */}
          <div className="flex items-center gap-2 sm:gap-3">
            
            {/* Language Switcher Dropdown */}
            <div className="relative" ref={langRef}>
              <button
                type="button"
                onClick={() => setLangMenuOpen(!langMenuOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 sm:px-3 sm:py-2 rounded-xl border border-ivory-200 hover:bg-ivory-100 text-xs sm:text-sm font-semibold text-navy-900 transition-colors"
                title="Select Language / भाषा चुनें"
                aria-expanded={langMenuOpen}
                aria-haspopup="true"
              >
                <Globe className="w-4 h-4 text-leaf-700" />
                <span>{currentLangObj.native}</span>
              </button>

              {langMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-civic-hover border border-ivory-200 py-1.5 z-50 max-h-72 overflow-y-auto">
                  <div className="px-3 py-1 text-[11px] font-bold text-navy-700/60 uppercase tracking-wider">
                    Select Language / भाषा
                  </div>
                  {LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => {
                        setLanguage(lang.code);
                        setLangMenuOpen(false);
                      }}
                      className={`w-full text-left px-3.5 py-2 text-sm flex items-center justify-between hover:bg-ivory-100 ${
                        currentLanguage === lang.code ? 'font-bold text-leaf-700 bg-leaf-50' : 'text-navy-900'
                      }`}
                    >
                      <span>{lang.native}</span>
                      <span className="text-xs text-navy-700/60">{lang.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Auth CTA / Dashboard */}
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <Link
                  to="/dashboard"
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-navy-900 hover:bg-navy-800 text-white text-xs sm:text-sm font-semibold transition-colors"
                >
                  <UserIcon className="w-4 h-4 text-saffron-500" />
                  <span className="hidden sm:inline">{user?.full_name?.split(' ')[0]}</span>
                </Link>
                {user?.role === 'admin' && (
                  <Link
                    to="/admin"
                    className="p-2 rounded-xl bg-amber-50 text-amber-900 hover:bg-amber-100 border border-amber-200"
                    title="Admin Verification Portal"
                  >
                    <ShieldCheck className="w-4 h-4 text-amber-700" />
                  </Link>
                )}
                <button
                  onClick={logout}
                  className="p-2 rounded-xl hover:bg-red-50 text-navy-700 hover:text-red-700 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-leaf-700 hover:bg-leaf-800 text-white text-xs sm:text-sm font-semibold shadow-sm transition-colors"
              >
                <UserIcon className="w-4 h-4" />
                <span>{t('nav_login')}</span>
              </Link>
            )}

            {/* Mobile Menu Toggle Button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl hover:bg-ivory-100 text-navy-900 focus:outline-none"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-ivory-200 bg-white px-4 pt-3 pb-6 space-y-3">
          <div className="space-y-1">
            <span className="text-[11px] font-bold text-navy-700/60 uppercase tracking-wider block px-2">
              Primary Navigation
            </span>
            {primaryNavLinks.map((link) => {
              const Icon = link.icon;
              const active = isActive(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold ${
                    active ? 'bg-leaf-50 text-leaf-800 border border-leaf-200' : 'text-navy-900 hover:bg-ivory-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-leaf-700' : 'text-navy-700'}`} />
                  {link.label}
                </Link>
              );
            })}
          </div>

          <div className="pt-2 border-t border-ivory-200 space-y-1">
            <span className="text-[11px] font-bold text-navy-700/60 uppercase tracking-wider block px-2">
              More Services
            </span>
            {secondaryNavLinks.map((sublink) => {
              const SubIcon = sublink.icon;
              const subActive = isActive(sublink.to);
              return (
                <Link
                  key={sublink.to}
                  to={sublink.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3.5 py-2 rounded-xl text-sm font-medium ${
                    subActive ? 'bg-leaf-50 text-leaf-800 font-bold' : 'text-navy-900/80 hover:bg-ivory-100'
                  }`}
                >
                  <SubIcon className={`w-4 h-4 ${subActive ? 'text-leaf-700' : 'text-navy-700/60'}`} />
                  {sublink.label}
                </Link>
              );
            })}
          </div>

          {isAuthenticated && (
            <div className="pt-2 border-t border-ivory-200">
              <Link
                to="/dashboard"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-navy-900 hover:bg-ivory-100"
              >
                <UserIcon className="w-4 h-4 text-saffron-500" />
                Citizen Dashboard
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
};
