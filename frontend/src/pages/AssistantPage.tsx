import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import {
  Citation,
  AssistantResponse,
  ExtractedProfile,
  EligibilityResult,
  SuggestedAction,
  MatchedScheme
} from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import {
  Mic,
  MicOff,
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  Volume2,
  VolumeX,
  Play,
  Pause,
  RotateCcw,
  FileText,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Info,
  ListChecks,
  Globe,
  Radio,
  Check,
  X
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  speechText?: string;
  citations?: Citation[];
  isFallback?: boolean;
  aiProvider?: string;
  extractedProfile?: ExtractedProfile;
  extractedFacts?: Record<string, any>;
  missingCriteria?: string[];
  followUpPrompt?: string | null;
  eligibilityResults?: EligibilityResult[];
  suggestedAction?: SuggestedAction | null;
  matchedSchemes?: MatchedScheme[];
  uncertaintyNotes?: string | null;
  nextSteps?: string[];
  applicationChecklist?: string[];
  detectedLanguage?: string;
  responseLanguage?: string;
  timestamp: string;
}

export const AssistantPage: React.FC = () => {
  const { currentLanguage } = useLanguage();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text:
        "Namaste! I am your JanSahayak Citizen Welfare Assistant. " +
        "You can speak or write in Hindi, English, or your local regional style. " +
        "Describe your occupation, family, land, income, or situation, and I will identify verified central and state welfare schemes that fit you, explain why, and help you prepare your application draft.",
      speechText:
        "Namaste! I am your JanSahayak Citizen Welfare Assistant. You can speak or write in Hindi or English. Describe your situation and I will guide you with verified government welfare schemes.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recognitionError, setRecognitionError] = useState<string | null>(null);

  // Transcript confirmation modal state
  const [transcriptModalOpen, setTranscriptModalOpen] = useState(false);
  const [pendingTranscript, setPendingTranscript] = useState('');

  // Audio Playback / TTS state
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [isSpeechPaused, setIsSpeechPaused] = useState(false);

  const [voiceStatus, setVoiceStatus] = useState<any>(null);
  const [assistantStatus, setAssistantStatus] = useState<any>(null);
  const [sessionProfile, setSessionProfile] = useState<ExtractedProfile>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [vStatus, aStatus] = await Promise.all([
          api.getVoiceStatus().catch(() => null),
          api.getAssistantStatus().catch(() => null)
        ]);
        if (vStatus) setVoiceStatus(vStatus);
        if (aStatus) setAssistantStatus(aStatus);
      } catch (err) {
        console.error('Could not fetch status:', err);
      }
    };
    fetchStatus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Clean up speech synthesis on unmount
  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
      }
    };
  }, []);

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || inputValue).trim();
    if (!textToSend || isLoading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputValue('');
    setIsLoading(true);

    try {
      const res: AssistantResponse = await api.chatAssistant(
        textToSend,
        undefined,
        currentLanguage,
        sessionProfile
      );

      // Accumulate confirmed extracted facts into multi-turn session state
      if (res.extracted_profile) {
        setSessionProfile((prev) => {
          const merged = { ...prev };
          for (const [k, v] of Object.entries(res.extracted_profile || {})) {
            if (v !== null && v !== undefined) {
              merged[k] = v;
            }
          }
          return merged;
        });
      }

      const botMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: res.answer || res.response_text || '',
        speechText: res.speech_text || res.answer || '',
        citations: res.citations || res.source_citations,
        isFallback: res.is_fallback,
        aiProvider: res.ai_provider,
        extractedProfile: res.extracted_profile,
        extractedFacts: res.extracted_facts,
        missingCriteria: res.missing_criteria || res.unknown_facts,
        followUpPrompt: res.follow_up_prompt,
        eligibilityResults: res.eligibility_results,
        suggestedAction: res.suggested_action,
        matchedSchemes: res.matched_schemes,
        uncertaintyNotes: res.uncertainty_notes,
        nextSteps: res.next_steps,
        applicationChecklist: res.application_checklist,
        detectedLanguage: res.detected_language,
        responseLanguage: res.response_language,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: "I encountered a temporary connection issue. Please try again or check the official government portals directly.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Voice Recognition Handler (Web Speech API with graceful fallback)
  const handleToggleMic = () => {
    const windowObj = window as any;
    const SpeechRecognition = windowObj.SpeechRecognition || windowObj.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setRecognitionError("Voice input is not supported in this browser. Please type your query.");
      setTimeout(() => setRecognitionError(null), 4000);
      return;
    }

    if (isRecording) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsRecording(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-IN';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      setIsRecording(true);
      setRecognitionError(null);

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setIsRecording(false);
        if (transcript && transcript.trim()) {
          // Open edit & confirm transcript modal before sending
          setPendingTranscript(transcript.trim());
          setTranscriptModalOpen(true);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
        setIsRecording(false);
        if (event.error === 'not-allowed') {
          setRecognitionError("Microphone access was denied. Please allow microphone permissions in your browser.");
        } else if (event.error !== 'no-speech') {
          setRecognitionError(`Voice recognition: ${event.error}`);
        }
        setTimeout(() => setRecognitionError(null), 4000);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.start();
    } catch (e: any) {
      console.error(e);
      setIsRecording(false);
      setRecognitionError("Could not start microphone. Please check browser settings.");
      setTimeout(() => setRecognitionError(null), 4000);
    }
  };

  const handleConfirmTranscript = () => {
    if (!pendingTranscript.trim()) return;
    const text = pendingTranscript.trim();
    setTranscriptModalOpen(false);
    setPendingTranscript('');
    handleSend(text);
  };

  // Audio Playback / Text-to-Speech Handler
  const handlePlaySpeech = (msgId: string, speechText: string, lang?: string) => {
    if (!('speechSynthesis' in window)) {
      alert("Text-to-speech audio playback is not supported in your browser.");
      return;
    }

    // If currently speaking this message and paused, resume
    if (speakingMessageId === msgId && isSpeechPaused) {
      window.speechSynthesis.resume();
      setIsSpeechPaused(false);
      return;
    }

    // Cancel any previous utterance
    window.speechSynthesis.cancel();

    // Clean text of any accidental markdown symbols or URLs
    const clean = speechText
      .replace(/[*_#`~>]/g, '')
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
      .replace(/https?:\/\/\S+/g, '')
      .trim();

    if (!clean) return;

    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = (lang === 'hi' || currentLanguage === 'hi') ? 'hi-IN' : 'en-IN';
    utterance.rate = 0.95; // Slightly slower, clearer speech for accessibility

    utterance.onend = () => {
      setSpeakingMessageId(null);
      setIsSpeechPaused(false);
    };

    utterance.onerror = () => {
      setSpeakingMessageId(null);
      setIsSpeechPaused(false);
    };

    setSpeakingMessageId(msgId);
    setIsSpeechPaused(false);
    window.speechSynthesis.speak(utterance);
  };

  const handlePauseSpeech = () => {
    if ('speechSynthesis' in window && speakingMessageId) {
      window.speechSynthesis.pause();
      setIsSpeechPaused(true);
    }
  };

  const handleStopSpeech = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setSpeakingMessageId(null);
      setIsSpeechPaused(false);
    }
  };

  const sampleQuestions = [
    {
      label: "🌾 Farmer Landholding (Bihar)",
      text: "A farmer from Bihar speaks in Bhojpuri and says they have three children, two bighas of land, and annual income around ₹1.5 lakh. Which government schemes might they qualify for?"
    },
    {
      label: "🛍️ Urban Street Vendor",
      text: "I am an urban street vendor selling vegetables on the footpath without a pucca shop. Can I get a micro-loan?"
    },
    {
      label: "🏠 Rural Kutcha Dwelling",
      text: "Rural family living in a kutcha house with income ₹1 lakh. Do we qualify for PMAY-G housing assistance?"
    },
    {
      label: "👴 Senior Citizen Health",
      text: "Senior citizen aged 72 with no BPL card. Does Ayushman Bharat PM-JAY cover me?"
    },
    {
      label: "🪙 APY Monthly Pension",
      text: "I am 28 years old working in a private shop and I do not pay income tax. Can I get a guaranteed pension under Atal Pension Yojana?"
    },
    {
      label: "🎓 Student Scholarship",
      text: "I am an OBC student studying in Class 10 with family income under ₹2 lakh. Am I eligible for PM-YASASVI scholarship?"
    }
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      
      {/* Top Banner / Independent Platform Disclosure */}
      <div className="rounded-xl p-3 bg-ivory-100/90 border border-ivory-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-navy-800">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-leaf-700 shrink-0" />
          <span>
            <strong>Independent Civic Guidance:</strong> JanSahayak is an autonomous citizen welfare assistant. Not an official government agency. Verified official records are cited directly from ministry portals.
          </span>
        </div>
        <div className="shrink-0 flex items-center gap-1.5 font-semibold text-leaf-800">
          <Globe className="w-3.5 h-3.5" />
          <span>Multilingual Voice Ready</span>
        </div>
      </div>

      {/* Main Title & Engine Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-softmint text-leaf-800 text-xs font-bold border border-leaf-200">
            <Sparkles className="w-3.5 h-3.5 text-leaf-700" />
            <span>Agentic Citizen Welfare Assistant • Voice-First</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight mt-1">
            Multilingual AI Welfare Assistant
          </h1>
          <p className="text-xs sm:text-sm text-navy-700/80 mt-0.5">
            Speak or type in your natural words to identify eligible schemes, verify criteria, and assemble application drafts.
          </p>
        </div>

        {/* Real-time Status Badge */}
        <div className="text-left sm:text-right">
          <Badge variant={assistantStatus?.groq_configured ? "verified" : "neutral"} size="sm">
            {assistantStatus?.groq_configured ? 'Groq Llama-3.3-70B Active' : 'Deterministic Rules & Browser Speech'}
          </Badge>
          <p className="text-[11px] text-navy-700/60 mt-0.5">
            Strict Non-Hallucinatory Grounding
          </p>
        </div>
      </div>

      {/* Error / Notification Banner if mic fails */}
      {recognitionError && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2 animate-fadeIn">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
          <span>{recognitionError}</span>
        </div>
      )}

      {/* Chat Container Card */}
      <Card className="flex flex-col h-[700px] p-4 sm:p-6 bg-white overflow-hidden shadow-civic border border-ivory-300">
        
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto space-y-5 pr-1.5 scrollbar-thin">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${
                msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              {/* Avatar Icon */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 text-white shadow-sm ${
                  msg.sender === 'user' ? 'bg-leaf-700' : 'bg-navy-900'
                }`}
              >
                {msg.sender === 'user' ? (
                  <UserIcon className="w-4 h-4" />
                ) : (
                  <Bot className="w-5 h-5 text-saffron-500" />
                )}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[94%] sm:max-w-[88%] rounded-2xl p-4 sm:p-5 text-sm leading-relaxed space-y-4 shadow-sm ${
                  msg.sender === 'user'
                    ? 'bg-leaf-50 text-navy-900 border border-leaf-200'
                    : 'bg-ivory-50/80 text-navy-900 border border-ivory-200'
                }`}
              >
                {/* Assistant Source Mode Header & Audio Bar */}
                {msg.sender === 'assistant' && (
                  <div className="flex items-center justify-between pb-2 border-b border-ivory-200/80 gap-2 flex-wrap">
                    <div className="flex items-center gap-2 text-xs">
                      {msg.isFallback ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-semibold text-[11px]">
                          <Info className="w-3.5 h-3.5 text-amber-700" />
                          <span>Verified Rule Engine Record</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-leaf-50 text-leaf-800 border border-leaf-200 font-semibold text-[11px]">
                          <Sparkles className="w-3.5 h-3.5 text-leaf-700" />
                          <span>Grounded AI Synthesis</span>
                        </span>
                      )}
                      {msg.responseLanguage && (
                        <span className="text-[10px] text-navy-700/60 uppercase font-mono">
                          [{msg.responseLanguage}]
                        </span>
                      )}
                    </div>

                    {/* Audio Playback Controls */}
                    <div className="flex items-center gap-1.5">
                      {speakingMessageId === msg.id ? (
                        <>
                          <button
                            onClick={isSpeechPaused ? () => handlePlaySpeech(msg.id, msg.speechText || msg.text, msg.responseLanguage) : handlePauseSpeech}
                            className="p-1.5 rounded-lg bg-leaf-100 text-leaf-800 hover:bg-leaf-200 text-xs flex items-center gap-1 font-semibold transition-colors"
                            title={isSpeechPaused ? "Resume speech" : "Pause speech"}
                          >
                            {isSpeechPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                            <span className="text-[11px]">{isSpeechPaused ? "Resume" : "Pause"}</span>
                          </button>
                          <button
                            onClick={handleStopSpeech}
                            className="p-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 text-xs flex items-center gap-1 font-semibold transition-colors"
                            title="Stop speech"
                          >
                            <VolumeX className="w-3.5 h-3.5" />
                            <span className="text-[11px]">Stop</span>
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => handlePlaySpeech(msg.id, msg.speechText || msg.text, msg.responseLanguage)}
                          className="px-2.5 py-1 rounded-lg bg-ivory-200 hover:bg-leaf-100 hover:text-leaf-800 text-navy-800 text-xs flex items-center gap-1.5 font-semibold transition-colors"
                          title="Listen to this explanation / आवाज़ सुनें"
                        >
                          <Volume2 className="w-3.5 h-3.5 text-leaf-700" />
                          <span className="text-[11px]">Read Aloud</span>
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Primary Narrative Text */}
                <div className="whitespace-pre-wrap leading-relaxed text-sm text-navy-950 font-normal">
                  {msg.text}
                </div>

                {/* 1. Structured Fact Classification Card (Confirmed, Inferred, Contradictions) */}
                {msg.extractedFacts && (msg.extractedFacts.confirmed || msg.extractedFacts.contradictions?.length > 0) && (
                  <div className="p-3.5 rounded-xl bg-white border border-ivory-300 space-y-2 text-xs">
                    <div className="font-bold text-navy-900 uppercase tracking-wide text-[10px] flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-leaf-800">
                        <CheckCircle2 className="w-3.5 h-3.5 text-leaf-700" />
                        <span>Profile Facts Extracted from Your Description:</span>
                      </span>
                      <span className="text-[10px] font-normal text-navy-700/60 lowercase">
                        no sensitive inferences
                      </span>
                    </div>

                    {/* Confirmed items grid */}
                    {Object.keys(msg.extractedFacts.confirmed || {}).length > 0 && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                        {Object.entries(msg.extractedFacts.confirmed).map(([key, val]) => (
                          <div key={key} className="p-2 rounded-lg bg-ivory-50 border border-ivory-200">
                            <span className="text-[10px] text-navy-700/60 block capitalize">
                              {key.replace(/_/g, ' ')}
                            </span>
                            <span className="font-bold text-navy-900">
                              {typeof val === 'number' && key.includes('income')
                                ? `₹${val.toLocaleString('en-IN')}`
                                : String(val)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Contradiction Warning (if any) */}
                    {msg.extractedFacts.contradictions && msg.extractedFacts.contradictions.length > 0 && (
                      <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 space-y-1">
                        <div className="flex items-center gap-1.5 text-red-900 font-bold text-[11px]">
                          <AlertTriangle className="w-3.5 h-3.5 text-red-600 shrink-0" />
                          <span>Conflicting Information Detected:</span>
                        </div>
                        {msg.extractedFacts.contradictions.map((c: string, idx: number) => (
                          <p key={idx} className="text-red-800 text-[11px] pl-5">• {c}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 2. Structured Matched Scheme Cards (Phase 4 & 5) */}
                {msg.matchedSchemes && msg.matchedSchemes.length > 0 && (
                  <div className="space-y-3 pt-1">
                    <span className="text-[11px] font-bold text-navy-900 uppercase tracking-wide flex items-center gap-1.5">
                      <ListChecks className="w-4 h-4 text-leaf-700" />
                      <span>Relevant Government Schemes Identified ({msg.matchedSchemes.length}):</span>
                    </span>

                    <div className="grid grid-cols-1 gap-3">
                      {msg.matchedSchemes.map((scheme, idx) => {
                        const schemeSlug = scheme.slug || scheme.scheme_slug || '';
                        const schemeName = scheme.name || scheme.scheme_name || 'Government Scheme';
                        const isEligible = scheme.eligibility_status === 'eligible';
                        const isPossible = scheme.eligibility_status === 'possibly_eligible';

                        return (
                          <div
                            key={idx}
                            className="p-4 rounded-xl bg-white border border-ivory-300 shadow-sm space-y-2.5 hover:border-leaf-300 transition-colors"
                          >
                            {/* Card Top: Title & Status Badge */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                              <div>
                                <h4 className="font-bold text-navy-950 text-sm">
                                  {schemeName}
                                </h4>
                                <p className="text-[11px] text-navy-700/70">
                                  {scheme.ministry || scheme.authority || 'Government of India'}
                                </p>
                              </div>

                              <Badge
                                variant={isEligible ? 'eligible' : isPossible ? 'possibly_eligible' : 'ineligible'}
                                size="sm"
                              >
                                {isEligible
                                  ? '✅ ELIGIBLE'
                                  : isPossible
                                  ? '⚠️ POTENTIALLY ELIGIBLE'
                                  : '❌ INELIGIBLE'}
                              </Badge>
                            </div>

                            {/* Benefit Summary */}
                            {scheme.benefit_summary && (
                              <div className="p-2 rounded-lg bg-leaf-50/60 border border-leaf-100 text-xs text-leaf-950">
                                <strong>Benefit:</strong> {scheme.benefit_summary}
                              </div>
                            )}

                            {/* Why It Fits */}
                            <div className="text-xs space-y-1">
                              <span className="font-semibold text-navy-900 block text-[11px]">
                                Why this fits your profile:
                              </span>
                              <p className="text-navy-700 text-[11px]">
                                {Array.isArray(scheme.why_it_fits)
                                  ? scheme.why_it_fits.join('; ')
                                  : scheme.why_it_fits}
                              </p>
                            </div>

                            {/* Missing info (if any) */}
                            {scheme.missing_information && scheme.missing_information.length > 0 && (
                              <div className="text-xs space-y-1 text-amber-900 bg-amber-50/70 p-2 rounded-lg border border-amber-100">
                                <span className="font-semibold text-[11px] flex items-center gap-1">
                                  <HelpCircle className="w-3.5 h-3.5 text-amber-700" />
                                  <span>Needed to verify official qualification:</span>
                                </span>
                                {scheme.missing_information.map((m: string, mIdx: number) => (
                                  <p key={mIdx} className="text-[11px] pl-4">• {m}</p>
                                ))}
                              </div>
                            )}

                            {/* Action Buttons: Prepare Application Draft & Portal Link */}
                            <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 border-t border-ivory-100 text-xs">
                              <button
                                onClick={() =>
                                  navigate('/applications', {
                                    state: {
                                      scheme_slug: schemeSlug,
                                      prefill: msg.extractedProfile || sessionProfile
                                    }
                                  })
                                }
                                className="py-2 px-3.5 rounded-lg bg-leaf-700 text-white hover:bg-leaf-800 font-bold flex items-center justify-center gap-1.5 transition-colors shadow-xs"
                              >
                                <FileText className="w-3.5 h-3.5" />
                                <span>Prepare Application Draft</span>
                                <ArrowRight className="w-3.5 h-3.5" />
                              </button>

                              {(scheme.official_url || scheme.official_source_url) && (
                                <a
                                  href={scheme.official_url || scheme.official_source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="py-2 px-3 rounded-lg bg-ivory-100 hover:bg-ivory-200 text-navy-800 font-semibold flex items-center justify-center gap-1.5 transition-colors border border-ivory-200"
                                >
                                  <span>Official Portal</span>
                                  <ExternalLink className="w-3 h-3 text-navy-700/60" />
                                </a>
                              )}
                            </div>

                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 3. Interactive Follow-Up Clarification Prompt */}
                {msg.followUpPrompt && (
                  <div className="p-3.5 rounded-xl bg-saffron-50 border border-saffron-200 space-y-2 text-xs">
                    <span className="font-bold text-saffron-900 flex items-center gap-1.5 text-[11px]">
                      <HelpCircle className="w-4 h-4 text-saffron-700 shrink-0" />
                      <span>Missing Information Needed for Official Qualification:</span>
                    </span>
                    <p className="text-saffron-950 font-medium">
                      {msg.followUpPrompt}
                    </p>
                  </div>
                )}

                {/* 4. Actionable Next Steps */}
                {msg.nextSteps && msg.nextSteps.length > 0 && (
                  <div className="p-3 rounded-xl bg-ivory-100 border border-ivory-200 space-y-1.5 text-xs">
                    <span className="font-bold text-navy-900 uppercase tracking-wide text-[10px] block">
                      Recommended Practical Next Steps:
                    </span>
                    <ul className="space-y-1 text-navy-800">
                      {msg.nextSteps.map((step, sIdx) => (
                        <li key={sIdx} className="flex items-start gap-1.5 text-[11px]">
                          <span className="font-bold text-leaf-800 shrink-0">{sIdx + 1}.</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 5. Verified Citations List */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="pt-2 border-t border-ivory-200 space-y-1.5 text-xs">
                    <span className="font-bold text-navy-900 text-[11px] uppercase tracking-wide flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-leaf-700" />
                      <span>Verified Official Portal Sources & Documents:</span>
                    </span>
                    <div className="space-y-1">
                      {msg.citations.map((c) => (
                        <a
                          key={c.citation_id}
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 rounded-lg bg-white border border-ivory-200 flex items-center justify-between hover:border-leaf-400 group transition-colors"
                        >
                          <div>
                            <span className="font-semibold text-leaf-800 text-[11px]">
                              [{c.citation_id}] {c.scheme_name}
                            </span>
                            <p className="text-[10px] text-navy-700/70">{c.authority}</p>
                          </div>
                          <ExternalLink className="w-3.5 h-3.5 text-navy-700/50 group-hover:text-leaf-700" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Bottom timestamp */}
                <div className="text-[10px] text-navy-700/50 text-right pt-1">
                  {msg.timestamp}
                </div>

              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-navy-900 text-white flex items-center justify-center">
                <Bot className="w-5 h-5 text-saffron-500" />
              </div>
              <div className="p-3.5 rounded-2xl bg-ivory-50 border border-ivory-200 text-xs text-navy-700 flex items-center gap-2">
                <div className="animate-spin w-4 h-4 border-2 border-leaf-700 border-t-transparent rounded-full" />
                <span>Extracting citizen facts, evaluating official rules, and preparing guidance...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Live Recording Pulse Banner */}
        {isRecording && (
          <div className="py-2.5 px-4 rounded-xl bg-red-50 border border-red-200 flex items-center justify-between animate-pulse my-2">
            <div className="flex items-center gap-2 text-red-800 text-xs font-bold">
              <Radio className="w-4 h-4 text-red-600 animate-spin" />
              <span>Listening to your voice... Speak clearly in Hindi or English</span>
            </div>
            <button
              onClick={handleToggleMic}
              className="px-2.5 py-1 rounded-lg bg-red-600 text-white text-xs font-semibold hover:bg-red-700"
            >
              Stop & Review
            </button>
          </div>
        )}

        {/* Suggested Realistic Citizen Scenarios */}
        {messages.length === 1 && (
          <div className="py-2.5 border-t border-ivory-200">
            <span className="text-[11px] font-bold text-navy-700/60 uppercase block mb-1.5">
              Try a realistic citizen scenario:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {sampleQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q.text)}
                  className="px-2.5 py-1.5 text-xs rounded-lg bg-ivory-100 hover:bg-leaf-50 hover:text-leaf-800 text-navy-800 transition-colors border border-ivory-200 text-left font-medium"
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Voice & Text Input Bar */}
        <div className="pt-3 border-t border-ivory-200">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            {/* Prominent Microphone Trigger */}
            <button
              type="button"
              onClick={handleToggleMic}
              className={`p-3 sm:px-4 sm:py-3 rounded-xl border font-bold flex items-center gap-2 transition-all ${
                isRecording
                  ? 'bg-red-500 border-red-600 text-white shadow-md animate-pulse'
                  : 'bg-saffron-50 border-saffron-300 text-saffron-800 hover:bg-saffron-100 active:scale-95'
              }`}
              title={isRecording ? 'Listening... click to stop' : 'Click to speak in Hindi or English'}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5 text-saffron-700" />}
              <span className="hidden sm:inline text-xs">
                {isRecording ? 'Listening...' : 'Speak'}
              </span>
            </button>

            {/* Input field */}
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Describe your situation (e.g. farmer with 2 acres in Bihar, street vendor, senior citizen)..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none bg-ivory-50/50 shadow-inner"
            />

            {/* Send Button */}
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!inputValue.trim() || isLoading}
              className="py-3 px-4 shadow-sm"
            >
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline ml-1 text-xs font-bold">Ask</span>
            </Button>
          </form>
        </div>

      </Card>

      {/* Transcript Review & Confirmation Modal */}
      {transcriptModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-ivory-300 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-ivory-200 pb-3">
              <div className="flex items-center gap-2 text-leaf-800 font-bold">
                <Mic className="w-5 h-5" />
                <span>Review Recognized Speech</span>
              </div>
              <button
                onClick={() => setTranscriptModalOpen(false)}
                className="text-navy-700/60 hover:text-navy-900"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-navy-700">
              Please review what was heard. You can edit any numbers, names, or words before sending to JanSahayak:
            </p>

            <textarea
              value={pendingTranscript}
              onChange={(e) => setPendingTranscript(e.target.value)}
              rows={4}
              className="w-full p-3 rounded-xl border border-ivory-300 text-sm font-medium focus:border-leaf-600 focus:outline-none bg-ivory-50/70"
            />

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  setTranscriptModalOpen(false);
                  setPendingTranscript('');
                  handleToggleMic();
                }}
                className="px-3.5 py-2 rounded-xl bg-ivory-100 hover:bg-ivory-200 text-navy-800 text-xs font-semibold flex items-center gap-1 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Re-record</span>
              </button>
              <button
                onClick={() => setTranscriptModalOpen(false)}
                className="px-3.5 py-2 rounded-xl border border-ivory-300 text-navy-700 text-xs font-semibold hover:bg-ivory-100 transition-colors"
              >
                Cancel
              </button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmTranscript}
                disabled={!pendingTranscript.trim()}
                className="px-4 py-2 font-bold flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Send to JanSahayak</span>
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
export default AssistantPage;
