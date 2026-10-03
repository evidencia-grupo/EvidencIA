/**
 * Telemetry event types, enums and allowlists for CBL Act Experiment.
 * Strict contract: zero PII, zero URLs, zero free text, zero network transmission.
 */

export type TelemetryCondition = 'A' | 'B';
export type TelemetryPhase = 'baseline' | 'assisted' | 'transfer';
export type EvidenceRelation = 'supports' | 'contradicts' | 'contextualizes' | 'unspecified';
export type UncertaintyKind = 'insufficient_evidence' | 'conflicting' | 'dated';
export type ReflectionInteraction = 'expanded' | 'answered' | 'dismissed';
export type DecisionStage = 'pre_evidence' | 'final';
export type DecisionVerdict = 'supported' | 'contradicted' | 'misleading' | 'insufficient' | 'cannot_determine';
export type VerificationStep = 'source' | 'date' | 'independent_evidence' | 'context' | 'none';
export type SessionEndReason = 'completed' | 'abandoned' | 'timeout';

export const PID_REGEX = /^P-[0-9]{4}$/;
export const SID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export const ITEM_ID_REGEX = /^IT-[0-9]{3}$/;
export const BUILD_HASH_REGEX = /^[a-f0-9]{7,12}$/;

// Strict allowlist: EventName -> exact allowed property keys in props
export const EVENT_ALLOWLIST = {
  session_started: ['build'],
  item_presented: ['n_claims'],
  claims_viewed: ['n_claims_visible'],
  claim_selected: ['claim_ordinal'],
  evidence_expanded: ['claim_ordinal', 'evidence_ordinal', 'relation'],
  source_opened: ['claim_ordinal', 'evidence_ordinal'],
  uncertainty_viewed: ['claim_ordinal', 'kind'],
  reflection_viewed: ['claim_ordinal', 'question_ordinal'],
  reflection_interacted: ['claim_ordinal', 'question_ordinal', 'interaction'],
  global_verdict_viewed: [],
  decision_submitted: ['claim_ordinal', 'stage', 'decision', 'confidence'],
  post_task_questionnaire: ['effort_seq', 'verification_steps'],
  session_ended: ['reason'],
} as const;

export type TelemetryEventName = keyof typeof EVENT_ALLOWLIST;

export interface SessionStartedProps {
  build: string;
}

export interface ItemPresentedProps {
  n_claims: number;
}

export interface ClaimsViewedProps {
  n_claims_visible: number;
}

export interface ClaimSelectedProps {
  claim_ordinal: number;
}

export interface EvidenceExpandedProps {
  claim_ordinal: number;
  evidence_ordinal: number;
  relation: EvidenceRelation;
}

export interface SourceOpenedProps {
  claim_ordinal: number;
  evidence_ordinal: number;
}

export interface UncertaintyViewedProps {
  claim_ordinal: number;
  kind: UncertaintyKind;
}

export interface ReflectionViewedProps {
  claim_ordinal: number;
  question_ordinal: number;
}

export interface ReflectionInteractedProps {
  claim_ordinal: number;
  question_ordinal: number;
  interaction: ReflectionInteraction;
}

export type GlobalVerdictViewedProps = Record<string, never>;

export interface DecisionSubmittedProps {
  claim_ordinal: number;
  stage: DecisionStage;
  decision: DecisionVerdict;
  confidence: number;
}

export interface PostTaskQuestionnaireProps {
  effort_seq: number;
  verification_steps: VerificationStep[];
}

export interface SessionEndedProps {
  reason: SessionEndReason;
}

export type TelemetryPropsMap = {
  session_started: SessionStartedProps;
  item_presented: ItemPresentedProps;
  claims_viewed: ClaimsViewedProps;
  claim_selected: ClaimSelectedProps;
  evidence_expanded: EvidenceExpandedProps;
  source_opened: SourceOpenedProps;
  uncertainty_viewed: UncertaintyViewedProps;
  reflection_viewed: ReflectionViewedProps;
  reflection_interacted: ReflectionInteractedProps;
  global_verdict_viewed: GlobalVerdictViewedProps;
  decision_submitted: DecisionSubmittedProps;
  post_task_questionnaire: PostTaskQuestionnaireProps;
  session_ended: SessionEndedProps;
};

export interface BaseTelemetryEnvelope<E extends TelemetryEventName> {
  schema_version: '1.0.0';
  pid: string;
  sid: string;
  cond: TelemetryCondition;
  phase: TelemetryPhase;
  item_id: string;
  event: E;
  seq: number;
  t_ms: number;
  props: TelemetryPropsMap[E];
  synthetic?: boolean;
}

export type TelemetryEvent = {
  [K in TelemetryEventName]: BaseTelemetryEnvelope<K>;
}[TelemetryEventName];
