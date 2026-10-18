import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { Citation, AssistantResponse, ExtractedProfile, EligibilityResult, SuggestedAction } from '../types';
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
  FileText,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Info
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
  isFallback?: boolean;
  aiProvider?: string;
  extractedProfile?: ExtractedProfile;
  missingCriteria?: string[];
  followUpPrompt?: string | null;
  eligibilityResults?: EligibilityResult[];
  suggestedAction?: SuggestedAction | null;
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
        "You can describe your situation in your own words (e.g., your occupation, family, land, income, or location). " +
        "I will extract your details, evaluate your eligibility using official rules, and help you prepare your application draft.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState<any>(null);
  const [assistantStatus, setAssistantStatus] = useState<any>(null);
  const [sessionProfile, setSessionProfile] = useState<ExtractedProfile>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
  }, [messages]);

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || inputValue;
    if (!textToSend.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: textToSend.trim(),
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
        text: res.answer,
        citations: res.citations,
        isFallback: res.is_fallback,
        aiProvider: res.ai_provider,
        extractedProfile: res.extracted_profile,
        missingCriteria: res.missing_criteria,
        followUpPrompt: res.follow_up_prompt,
        eligibilityResults: res.eligibility_results,
        suggestedAction: res.suggested_action,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'assistant',
        text: "I encountered an error connecting to the welfare document database. Please try again or check the official government portal.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleMic = () => {
    const windowObj = window as any;
    const SpeechRecognition = windowObj.SpeechRecognition || windowObj.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice recognition is not supported in this browser. Please type your query.");
      return;
    }

    if (isRecording) {
      setIsRecording(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-IN';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      setIsRecording(true);

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsRecording(false);
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.start();
    } catch (e) {
      console.error(e);
      setIsRecording(false);
    }
  };

  const handleSpeak = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      // Remove markdown tags for smoother speech
      const cleanText = text.replace(/[*#_`>]/g, '');
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-IN';
      window.speechSynthesis.speak(utterance);
    }
  };

  const sampleQuestions = [
    "A farmer from Bihar speaks in Bhojpuri and says they have three children, two bighas of land, and annual income around ₹1.5 lakh. Which government schemes might they qualify for?",
    "I am an urban street vendor with no pucca shop. Can I get a micro-loan?",
    "Rural family living in a kutcha house with income ₹1 lakh. Do we qualify for PMAY-G?",
    "Senior citizen aged 72 with no BPL card. Does Ayushman Bharat PM-JAY cover me?"
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-softmint text-leaf-800 text-xs font-bold border border-leaf-200">
            <Sparkles className="w-3.5 h-3.5 text-leaf-700" />
            <span>Phase 1 Grounded RAG & Fact Extraction</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-900 tracking-tight mt-1">
            Multilingual Welfare Assistant
          </h1>
        </div>

        {/* Real-time Status Badge */}
        <div className="text-right">
          <Badge variant={assistantStatus?.groq_configured ? "verified" : "neutral"} size="sm">
            {assistantStatus?.groq_configured ? 'Groq Llama-3.3-70B Online' : 'Deterministic Rules & Browser Speech'}
          </Badge>
          <p className="text-[11px] text-navy-700/60 mt-0.5">
            Strict Non-Hallucinatory Grounding
          </p>
        </div>
      </div>

      {/* Main Chat Thread */}
      <Card className="flex flex-col h-[640px] p-4 sm:p-6 bg-white overflow-hidden shadow-civic">
        
        {/* Messages scroll area */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${
                msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-white ${
                  msg.sender === 'user' ? 'bg-leaf-700' : 'bg-navy-900'
                }`}
              >
                {msg.sender === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4 text-saffron-500" />}
              </div>

              <div
                className={`max-w-[92%] sm:max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed space-y-3 ${
                  msg.sender === 'user'
                    ? 'bg-leaf-50 text-navy-900 border border-leaf-200'
                    : 'bg-ivory-50/70 text-navy-900 border border-ivory-200'
                }`}
              >
                {/* AI / Fallback mode disclosure banner for assistant messages */}
                {msg.sender === 'assistant' && msg.id !== 'welcome' && (
                  <div className={`p-2 rounded-lg text-xs flex items-center gap-2 ${
                    msg.isFallback
                      ? 'bg-amber-50 text-amber-900 border border-amber-200'
                      : 'bg-leaf-50 text-leaf-900 border border-leaf-200'
                  }`}>
                    {msg.isFallback ? (
                      <>
                        <Info className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                        <span><strong>Rule Engine Active:</strong> Synthesized from verified official scheme criteria.</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5 text-leaf-700 shrink-0" />
                        <span><strong>Grounded AI:</strong> Powered by Groq Llama-3.3-70B with official evidence citations.</span>
                      </>
                    )}
                  </div>
                )}

                {/* Main answer text */}
                <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>

                {/* 1. Structured Fact Extraction Card */}
                {msg.extractedProfile && (
                  (msg.extractedProfile.occupation || msg.extractedProfile.state || msg.extractedProfile.annual_income || msg.extractedProfile.landholding_raw) && (
                    <div className="p-3 rounded-xl bg-white border border-ivory-300 space-y-1.5 text-xs">
                      <div className="font-bold text-navy-900 uppercase tracking-wide text-[10px] flex items-center gap-1.5 text-leaf-800">
                        <CheckCircle2 className="w-3.5 h-3.5 text-leaf-700" />
                        <span>Extracted Citizen Facts (Confirmed from Input):</span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                        {msg.extractedProfile.state && (
                          <div className="p-2 rounded-lg bg-ivory-50 border border-ivory-200">
                            <span className="text-[10px] text-navy-700/60 block">State</span>
                            <span className="font-bold text-navy-900">{msg.extractedProfile.state}</span>
                          </div>
                        )}
                        {msg.extractedProfile.occupation && (
                          <div className="p-2 rounded-lg bg-ivory-50 border border-ivory-200">
                            <span className="text-[10px] text-navy-700/60 block">Occupation</span>
                            <span className="font-bold text-navy-900 capitalize">{msg.extractedProfile.occupation}</span>
                          </div>
                        )}
                        {msg.extractedProfile.annual_income !== null && msg.extractedProfile.annual_income !== undefined && (
                          <div className="p-2 rounded-lg bg-ivory-50 border border-ivory-200">
                            <span className="text-[10px] text-navy-700/60 block">Annual Income</span>
                            <span className="font-bold text-navy-900">₹{msg.extractedProfile.annual_income.toLocaleString('en-IN')}</span>
                          </div>
                        )}
                        {msg.extractedProfile.landholding_raw && (
                          <div className="p-2 rounded-lg bg-ivory-50 border border-ivory-200">
                            <span className="text-[10px] text-navy-700/60 block">Landholding</span>
                            <span className="font-bold text-navy-900">{msg.extractedProfile.landholding_raw}</span>
                          </div>
                        )}
                      </div>
                      {msg.extractedProfile.landholding_notes && (
                        <p className="text-[11px] text-navy-700/70 italic pt-1">
                          * {msg.extractedProfile.landholding_notes}
                        </p>
                      )}
                    </div>
                  )
                )}

                {/* 2. Interactive Follow-Up Clarification Prompt */}
                {msg.followUpPrompt && (
                  <div className="p-3 rounded-xl bg-saffron-50 border border-saffron-200 space-y-2 text-xs">
                    <span className="font-bold text-saffron-900 flex items-center gap-1.5 text-[11px]">
                      <HelpCircle className="w-4 h-4 text-saffron-700 shrink-0" />
                      <span>Missing Information Needed for Official Qualification:</span>
                    </span>
                    <p className="text-saffron-950 font-medium">
                      {msg.followUpPrompt}
                    </p>
                  </div>
                )}

                {/* 3. Actionable Application Draft Button */}
                {msg.suggestedAction && (
                  <div className="pt-1">
                    <button
                      onClick={() =>
                        navigate('/apply', {
                          state: {
                            scheme_slug: msg.suggestedAction?.scheme_slug,
                            prefill: msg.suggestedAction?.prefill_data
                          }
                        })
                      }
                      className="w-full py-2.5 px-4 rounded-xl bg-leaf-700 text-white hover:bg-leaf-800 text-xs font-bold shadow-sm flex items-center justify-center gap-2 transition-colors"
                    >
                      <FileText className="w-4 h-4" />
                      <span>Prepare Application Draft for {msg.suggestedAction.scheme_name}</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                )}

                {/* Text-to-speech button */}
                {msg.sender === 'assistant' && (
                  <div className="pt-1 flex items-center justify-between text-xs text-navy-700/60">
                    <button
                      onClick={() => handleSpeak(msg.text)}
                      className="inline-flex items-center gap-1 hover:text-leaf-700 font-semibold text-[11px]"
                      title="Listen in speech / आवाज़ सुनें"
                    >
                      <Volume2 className="w-3.5 h-3.5" />
                      <span>Listen</span>
                    </button>
                    <span>{msg.timestamp}</span>
                  </div>
                )}

                {/* Verified Citations List */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="pt-2 border-t border-ivory-200 space-y-1.5 text-xs">
                    <span className="font-bold text-navy-900 text-[11px] uppercase tracking-wide flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-leaf-700" />
                      <span>Verified Official Portal Sources:</span>
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

              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-navy-900 text-white flex items-center justify-center">
                <Bot className="w-4 h-4 text-saffron-500" />
              </div>
              <div className="p-3.5 rounded-2xl bg-ivory-50 border border-ivory-200 text-xs text-navy-700 flex items-center gap-2">
                <div className="animate-spin w-4 h-4 border-2 border-leaf-700 border-t-transparent rounded-full" />
                <span>Extracting facts, retrieving official documents, and evaluating rules...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Queries */}
        {messages.length === 1 && (
          <div className="py-2 border-t border-ivory-100">
            <span className="text-[11px] font-bold text-navy-700/60 uppercase block mb-1.5">
              Try a realistic citizen query:
            </span>
            <div className="flex flex-col sm:flex-row flex-wrap gap-1.5">
              {sampleQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="px-2.5 py-1.5 text-xs rounded-lg bg-ivory-100 hover:bg-leaf-50 hover:text-leaf-800 text-navy-800 transition-colors border border-ivory-200 text-left line-clamp-1"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Bar */}
        <div className="pt-3 border-t border-ivory-200">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <button
              type="button"
              onClick={handleToggleMic}
              className={`p-3 rounded-xl border transition-colors ${
                isRecording
                  ? 'bg-red-50 border-red-300 text-red-600 animate-pulse'
                  : 'bg-saffron-50 border-saffron-200 text-saffron-700 hover:bg-saffron-100'
              }`}
              title={isRecording ? 'Listening... click to stop' : 'Click to speak in your language'}
            >
              {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Describe your situation (e.g. occupation, land, income, state)..."
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 rounded-xl border border-ivory-300 text-sm focus:border-leaf-600 focus:outline-none bg-ivory-50/50"
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!inputValue.trim() || isLoading}
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>

      </Card>

    </div>
  );
};
