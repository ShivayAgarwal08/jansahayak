import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLanguage, LANGUAGES } from '../../context/LanguageContext';
import {
  Compass,
  FileCheck2,
  Mic,
  FileText,
  AlertCircle,
  User as UserIcon,
  Globe,
  Menu,
  X,
  Sparkles,
  LogOut,
  ShieldCheck
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const { currentLanguage, setLanguage, t } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { to: '/schemes', label: t('nav_schemes'), icon: Compass },
    { to: '/eligibility', label: t('nav_eligibility'), icon: FileCheck2 },
    { to: '/assistant', label: t('nav_assistant'), icon: Mic },
    { to: '/applications', label: 'Application Prep', icon: FileText },
    { to: '/rti', label: t('nav_rti'), icon: FileText },
    { to: '/grievances', label: t('nav_grievance'), icon: AlertCircle },
  ];

  const currentLangObj = LANGUAGES.find((l) => l.code === currentLanguage) || LANGUAGES[0];

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-ivory-200">
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
          <nav className="hidden lg:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const active = isActive(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold transition-colors ${
                    active
                      ? 'bg-leaf-50 text-leaf-800 border border-leaf-200/80'
                      : 'text-navy-900/80 hover:text-navy-900 hover:bg-ivory-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-leaf-700' : 'text-navy-700/60'}`} />
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Right Action Items */}
          <div className="flex items-center gap-2 sm:gap-3">
            
            {/* Language Switcher Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setLangMenuOpen(!langMenuOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 sm:px-3 sm:py-2 rounded-xl border border-ivory-200 hover:bg-ivory-100 text-xs sm:text-sm font-semibold text-navy-900 transition-colors"
                title="Select Language / भाषा चुनें"
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
        <div className="lg:hidden border-t border-ivory-200 bg-white px-4 pt-3 pb-6 space-y-1.5">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.to);
            return (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-base font-semibold ${
                  active ? 'bg-leaf-50 text-leaf-800 border border-leaf-200' : 'text-navy-900 hover:bg-ivory-100'
                }`}
              >
                <Icon className={`w-5 h-5 ${active ? 'text-leaf-700' : 'text-navy-700'}`} />
                {link.label}
              </Link>
            );
          })}
          {isAuthenticated && (
            <Link
              to="/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-base font-semibold text-navy-900 hover:bg-ivory-100"
            >
              <UserIcon className="w-5 h-5 text-saffron-500" />
              Citizen Dashboard
            </Link>
          )}
        </div>
      )}
    </header>
  );
};
