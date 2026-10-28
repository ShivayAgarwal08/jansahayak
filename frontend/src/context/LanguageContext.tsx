import React, { createContext, useContext, useState } from 'react';

export interface Language {
  code: string;
  name: string;
  native: string;
}

export const LANGUAGES: Language[] = [
  { code: 'en', name: 'English', native: 'English' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
  { code: 'bn', name: 'Bengali', native: 'বাংলা' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు' },
  { code: 'mr', name: 'Marathi', native: 'मराठी' },
  { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'ml', name: 'Malayalam', native: 'മലയാളം' },
  { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
  { code: 'or', name: 'Odia', native: 'ଓଡ଼ିଆ' },
];

const TRANSLATIONS: Record<string, Record<string, string>> = {
  en: {
    nav_home: 'Home',
    nav_find_schemes: 'Find Schemes',
    nav_ai_assistant: 'AI Assistant',
    nav_applications: 'My Applications',
    nav_more_services: 'More Services',
    nav_schemes: 'Discover Schemes',
    nav_eligibility: 'Eligibility Calculator',
    nav_compare: 'Compare Schemes',
    nav_assistant: 'AI Assistant',
    nav_rti: 'RTI Drafter (Sec 6(1))',
    nav_grievance: 'Public Grievance (CPGRAMS)',
    nav_dashboard: 'Citizen Dashboard',
    nav_login: 'Login / Register',
    hero_title: 'Welfare Schemes Made Simple in Your Language',
    hero_subtitle: 'Discover verified government benefits, check deterministic eligibility, and prepare application documents with confidence.',
    cta_explore: 'Explore Schemes',
    cta_voice: 'Ask Voice Assistant',
    badge_verified: 'Official Guidelines Verified',
  },
  hi: {
    nav_home: 'होम',
    nav_find_schemes: 'योजनाएं खोजें',
    nav_ai_assistant: 'एआई सहायक',
    nav_applications: 'मेरे आवेदन',
    nav_more_services: 'अन्य सेवाएं',
    nav_schemes: 'योजनाएं खोजें',
    nav_eligibility: 'पात्रता कैलकुलेटर',
    nav_compare: 'योजना तुलना',
    nav_assistant: 'एआई सहायक',
    nav_rti: 'आरटीआई ड्राफ्ट (धारा 6(1))',
    nav_grievance: 'जन शिकायत (CPGRAMS)',
    nav_dashboard: 'नागरिक डैशबोर्ड',
    nav_login: 'लॉग इन / पंजीकरण',
    hero_title: 'आपकी भाषा में सरकारी योजनाएं और नागरिक सेवाएं',
    hero_subtitle: 'सत्यापित सरकारी योजनाओं की खोज करें, सटीक पात्रता नियम जांचें और आत्मविश्वास से अपने आवेदन दस्तावेज तैयार करें।',
    cta_explore: 'योजनाएं देखें',
    cta_voice: 'आवाज़ से पूछें',
    badge_verified: 'सत्यापित मार्गदर्शिका रिकॉर्ड',
  },
};

interface LanguageContextType {
  currentLanguage: string;
  setLanguage: (lang: string) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentLanguage, setCurrentLanguage] = useState<string>(
    localStorage.getItem('jansahayak_lang') || 'en'
  );

  const setLanguage = (lang: string) => {
    setCurrentLanguage(lang);
    localStorage.setItem('jansahayak_lang', lang);
  };

  const t = (key: string): string => {
    if (TRANSLATIONS[currentLanguage] && TRANSLATIONS[currentLanguage][key]) {
      return TRANSLATIONS[currentLanguage][key];
    }
    return TRANSLATIONS['en'][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ currentLanguage, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
