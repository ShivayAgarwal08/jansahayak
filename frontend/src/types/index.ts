export interface User {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  role: 'citizen' | 'admin';
  preferred_language: string;
  state?: string;
  district?: string;
  is_active: boolean;
  created_at: string;
}

export interface SchemeSource {
  id: number;
  source_title: string;
  source_url: string;
  issuing_authority: string;
  document_reference?: string;
  verified_at: string;
}

export interface Scheme {
  id: number;
  slug: string;
  name: string;
  name_hi?: string;
  summary: string;
  summary_hi?: string;
  department: string;
  scope: 'central' | 'state';
  applicable_states: string[];
  category: string;
  beneficiary_types: string[];
  benefits_summary: string;
  eligibility_rules: Record<string, any>;
  exclusions: string[];
  required_documents: Array<{
    name: string;
    mandatory: boolean;
    alternatives: string[];
  }>;
  application_steps: string[];
  official_portal_url: string;
  verification_status: 'verified' | 'under_review' | 'deprecated';
  last_verified_at: string;
  sources?: SchemeSource[];
}

export interface ConditionEvaluation {
  criterion: string;
  official_rule?: string;
  citizen_value?: any;
  reason?: string;
}

export interface UnknownCondition {
  criterion: string;
  prompt: string;
}

export interface EligibilityResult {
  scheme_id: number;
  scheme_slug: string;
  scheme_name: string;
  status: 'eligible' | 'possibly_eligible' | 'ineligible';
  summary_explanation: string;
  satisfied_conditions: ConditionEvaluation[];
  unsatisfied_conditions: ConditionEvaluation[];
  unknown_conditions: UnknownCondition[];
  applicable_exclusions: string[];
  official_sources: Array<{ title: string; url: string; authority?: string }>;
  next_steps: string[];
  assessed_at: string;
  disclaimer: string;
}

export interface ApplicationDraft {
  id: number;
  user_id: number;
  scheme_id: number;
  title: string;
  applicant_details: Record<string, any>;
  checklist_state: Record<string, boolean>;
  status: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  scheme?: Scheme;
}

export interface RtiDraft {
  id: number;
  user_id: number;
  public_authority: string;
  subject: string;
  information_requested: string;
  time_period?: string;
  applicant_name: string;
  state: string;
  preferred_language: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface GrievanceDraft {
  id: number;
  user_id: number;
  department: string;
  category: string;
  description: string;
  previous_complaint_ref?: string;
  desired_resolution: string;
  applicant_name: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  citation_id: number;
  scheme_slug: string;
  scheme_name: string;
  title: string;
  authority: string;
  url: string;
  page_number: number;
}

export interface ExtractedProfile {
  state?: string | null;
  district?: string | null;
  occupation?: string | null;
  age?: number | null;
  gender?: string | null;
  annual_income?: number | null;
  owns_cultivable_land?: boolean | null;
  landholding_raw?: string | null;
  landholding_acres?: number | null;
  landholding_notes?: string | null;
  family_details?: Record<string, any>;
  housing_type?: string | null;
  area_type?: string | null;
  is_bpl?: boolean | null;
  is_govt_employee?: boolean | null;
  pays_income_tax?: boolean | null;
  [key: string]: any;
}

export interface SuggestedAction {
  action: string;
  scheme_slug: string;
  scheme_name: string;
  status: string;
  prefill_data: Record<string, any>;
}

export interface MatchedScheme {
  slug?: string;
  scheme_slug?: string;
  name?: string;
  scheme_name?: string;
  ministry?: string;
  authority?: string;
  benefit_summary?: string;
  eligibility_status: string;
  why_it_fits: string | string[];
  missing_information?: string[];
  official_url?: string;
  official_source_url?: string;
  action_label?: string;
  action_url?: string;
  action_prefill?: Record<string, any>;
}

export interface AssistantResponse {
  answer: string;
  citations: Citation[];
  model: string;
  is_fallback: boolean;
  status: string;
  ai_provider?: string;
  fallback_reason?: string | null;
  extracted_profile?: ExtractedProfile;
  missing_criteria?: string[];
  follow_up_prompt?: string | null;
  eligibility_results?: EligibilityResult[];
  suggested_action?: SuggestedAction | null;

  // Agentic structured fields (Phase 4)
  detected_language?: string;
  response_language?: string;
  extracted_facts?: Record<string, any>;
  unknown_facts?: string[];
  clarifying_questions?: string[];
  matched_schemes?: MatchedScheme[];
  match_reasons?: string[];
  eligibility_status?: string;
  uncertainty_notes?: string | null;
  source_citations?: Citation[];
  next_steps?: string[];
  application_checklist?: string[];
  response_text?: string;
  speech_text?: string;
}

export interface AssistantStatus {
  groq_configured: boolean;
  groq_model: string;
  ai_provider: string;
  fallback_available: boolean;
  status: string;
}
