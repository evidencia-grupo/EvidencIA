/**
 * Strict fail-closed event sanitizer for CBL Act telemetry.
 * Discards and counts any malformed, out-of-range, PII-bearing or unexpected event.
 * Never mutates or fixes invalid data.
 */

import {
  BUILD_HASH_REGEX,
  EVENT_ALLOWLIST,
  ITEM_ID_REGEX,
  PID_REGEX,
  SID_REGEX,
  TelemetryEvent,
  TelemetryEventName,
} from './events';

export interface ValidationSuccess {
  ok: true;
  event: TelemetryEvent;
}

export interface ValidationFailure {
  ok: false;
  reason: string;
}

export type ValidationResult = ValidationSuccess | ValidationFailure;

// Rejection counters for auditability and data integrity tracking
const rejectionStats: Record<string, number> = {};

export function recordRejection(reason: string): void {
  rejectionStats[reason] = (rejectionStats[reason] || 0) + 1;
}

export function getRejectionStats(): Record<string, number> {
  return { ...rejectionStats };
}

export function resetRejectionStats(): void {
  for (const key of Object.keys(rejectionStats)) {
    delete rejectionStats[key];
  }
}

// Security patterns for untrusted strings
const URL_PATTERN = /(?:https?:\/\/|www\.)[^\s/$.?#].[^\s]*/i;
const EMAIL_PATTERN = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
const CPF_PATTERN = /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/;

const FORBIDDEN_KEYS = new Set([
  'text',
  'transcript',
  'url',
  'video_id',
  'videoId',
  'name',
  'email',
  'cpf',
  'comment',
  'query',
  'title',
  'message',
]);

const REQUIRED_ENVELOPE_KEYS = new Set([
  'schema_version',
  'pid',
  'sid',
  'cond',
  'phase',
  'item_id',
  'event',
  'seq',
  't_ms',
  'props',
]);

const ALLOWED_ENVELOPE_KEYS = new Set([
  ...REQUIRED_ENVELOPE_KEYS,
  'synthetic',
]);

function isObject(val: unknown): val is Record<string, unknown> {
  return typeof val === 'object' && val !== null && !Array.isArray(val);
}

function isSafeString(val: unknown, maxLen = 64): val is string {
  if (typeof val !== 'string') return false;
  if (val.length === 0 || val.length > maxLen) return false;
  if (URL_PATTERN.test(val)) return false;
  if (EMAIL_PATTERN.test(val)) return false;
  if (CPF_PATTERN.test(val)) return false;
  return true;
}

function isIntegerInRange(val: unknown, min: number, max: number): val is number {
  return typeof val === 'number' && Number.isInteger(val) && val >= min && val <= max;
}

export function validateEvent(raw: unknown): ValidationResult {
  if (!isObject(raw)) {
    recordRejection('not_an_object');
    return { ok: false, reason: 'Event must be a non-null object' };
  }

  // 1. Check envelope keys: no unknown keys, no missing required keys
  const rawKeys = Object.keys(raw);
  for (const key of rawKeys) {
    if (!ALLOWED_ENVELOPE_KEYS.has(key)) {
      recordRejection('unknown_envelope_key');
      return { ok: false, reason: `Unknown envelope key: ${key}` };
    }
  }

  for (const requiredKey of REQUIRED_ENVELOPE_KEYS) {
    if (!(requiredKey in raw)) {
      recordRejection('missing_envelope_key');
      return { ok: false, reason: `Missing envelope key: ${requiredKey}` };
    }
  }

  // 2. Validate envelope types
  if (raw.schema_version !== '1.0.0') {
    recordRejection('invalid_schema_version');
    return { ok: false, reason: `Invalid schema_version: expected "1.0.0", got ${String(raw.schema_version)}` };
  }

  if (typeof raw.pid !== 'string' || !PID_REGEX.test(raw.pid)) {
    recordRejection('invalid_pid');
    return { ok: false, reason: `Invalid pid format: expected ^P-[0-9]{4}$, got ${String(raw.pid)}` };
  }

  if (typeof raw.sid !== 'string' || !SID_REGEX.test(raw.sid)) {
    recordRejection('invalid_sid');
    return { ok: false, reason: `Invalid sid format: expected UUID v4, got ${String(raw.sid)}` };
  }

  if (raw.cond !== 'A' && raw.cond !== 'B') {
    recordRejection('invalid_condition');
    return { ok: false, reason: `Invalid cond: expected "A" or "B", got ${String(raw.cond)}` };
  }

  if (raw.phase !== 'baseline' && raw.phase !== 'assisted' && raw.phase !== 'transfer') {
    recordRejection('invalid_phase');
    return { ok: false, reason: `Invalid phase: expected baseline|assisted|transfer, got ${String(raw.phase)}` };
  }

  if (typeof raw.item_id !== 'string' || !ITEM_ID_REGEX.test(raw.item_id)) {
    recordRejection('invalid_item_id');
    return { ok: false, reason: `Invalid item_id format: expected ^IT-[0-9]{3}$, got ${String(raw.item_id)}` };
  }

  const eventName = raw.event;
  if (typeof eventName !== 'string' || !(eventName in EVENT_ALLOWLIST)) {
    recordRejection('unknown_event');
    return { ok: false, reason: `Unknown event name: ${String(eventName)}` };
  }

  if (typeof raw.seq !== 'number' || !Number.isInteger(raw.seq) || raw.seq < 0) {
    recordRejection('invalid_seq');
    return { ok: false, reason: `Invalid seq: expected non-negative integer, got ${String(raw.seq)}` };
  }

  if (typeof raw.t_ms !== 'number' || !Number.isFinite(raw.t_ms) || raw.t_ms < 0) {
    recordRejection('invalid_t_ms');
    return { ok: false, reason: `Invalid t_ms: expected non-negative number, got ${String(raw.t_ms)}` };
  }

  // 3. Validate props object
  const props = raw.props;
  if (!isObject(props)) {
    recordRejection('props_not_an_object');
    return { ok: false, reason: 'props must be a non-null object' };
  }

  // Check for forbidden keys anywhere in props
  for (const pKey of Object.keys(props)) {
    if (FORBIDDEN_KEYS.has(pKey)) {
      recordRejection('forbidden_key_in_props');
      return { ok: false, reason: `Forbidden key in props: ${pKey}` };
    }
  }

  const allowedPropKeys = EVENT_ALLOWLIST[eventName as TelemetryEventName] as readonly string[];
  const actualPropKeys = Object.keys(props);

  if (actualPropKeys.length !== allowedPropKeys.length) {
    recordRejection('prop_keys_count_mismatch');
    return {
      ok: false,
      reason: `Expected ${allowedPropKeys.length} prop keys for event ${eventName}, got ${actualPropKeys.length}`,
    };
  }

  for (const allowedKey of allowedPropKeys) {
    if (!(allowedKey in props)) {
      recordRejection('missing_prop_key');
      return { ok: false, reason: `Missing prop key "${allowedKey}" for event ${eventName}` };
    }
  }

  for (const actualKey of actualPropKeys) {
    if (!allowedPropKeys.includes(actualKey)) {
      recordRejection('unknown_prop_key');
      return { ok: false, reason: `Unknown prop key "${actualKey}" for event ${eventName}` };
    }
  }

  // 4. Validate specific props contents per event
  const typedEventName = eventName as TelemetryEventName;
  switch (typedEventName) {
    case 'session_started': {
      if (!isSafeString(props.build, 16) || !BUILD_HASH_REGEX.test(props.build)) {
        recordRejection('invalid_build_hash');
        return { ok: false, reason: 'Invalid build hash in session_started' };
      }
      break;
    }

    case 'item_presented': {
      if (!isIntegerInRange(props.n_claims, 1, 10)) {
        recordRejection('invalid_n_claims');
        return { ok: false, reason: 'n_claims must be an integer between 1 and 10' };
      }
      break;
    }

    case 'claims_viewed': {
      if (!isIntegerInRange(props.n_claims_visible, 1, 10)) {
        recordRejection('invalid_n_claims_visible');
        return { ok: false, reason: 'n_claims_visible must be an integer between 1 and 10' };
      }
      break;
    }

    case 'claim_selected': {
      if (!isIntegerInRange(props.claim_ordinal, 1, 10)) {
        recordRejection('invalid_claim_ordinal');
        return { ok: false, reason: 'claim_ordinal must be an integer between 1 and 10' };
      }
      break;
    }

    case 'evidence_expanded': {
      if (!isIntegerInRange(props.claim_ordinal, 1, 10)) {
        recordRejection('invalid_claim_ordinal');
        return { ok: false, reason: 'claim_ordinal must be an integer between 1 and 10' };
      }
      if (!isIntegerInRange(props.evidence_ordinal, 1, 20)) {
        recordRejection('invalid_evidence_ordinal');
        return { ok: false, reason: 'evidence_ordinal must be an integer between 1 and 20' };
      }
      const allowedRelations = ['supports', 'contradicts', 'contextualizes', 'unspecified'];
      if (typeof props.relation !== 'string' || !allowedRelations.includes(props.relation)) {
        recordRejection('invalid_evidence_relation');
        return { ok: false, reason: `Invalid relation: ${String(props.relation)}` };
      }
      break;
    }

    case 'source_opened': {
      if (!isIntegerInRange(props.claim_ordinal, 1, 10)) {
        recordRejection('invalid_claim_ordinal');
        return { ok: false, reason: 'claim_ordinal must be an integer between 1 and 10' };
      }
      if (!isIntegerInRange(props.evidence_ordinal, 1, 20)) {
        recordRejection('invalid_evidence_ordinal');
        return { ok: false, reason: 'evidence_ordinal must be an integer between 1 and 20' };
      }
      break;
    }

    case 'uncertainty_viewed': {
      if (!isIntegerInRange(props.claim_ordinal, 1, 10)) {
        recordRejection('invalid_claim_ordinal');
        return { ok: false, reason: 'claim_ordinal must be an integer between 1 and 10' };
      }
      const allowedKinds = ['insufficient_evidence', 'conflicting', 'dated'];
      if (typeof props.kind !== 'string' || !allowedKinds.includes(props.kind)) {
        recordRejection('invalid_uncertainty_kind');
        return { ok: false, reason: `Invalid uncertainty kind: ${String(props.kind)}` };
      }
      break;
    }

    case 'reflection_viewed': {
      if (!isIntegerInRange(props.claim_ordinal, 1, 10)) {
        recordRejection('invalid_claim_ordinal');
        return { ok: false, reason: 'claim_ordinal must be an integer between 1 and 10' };
      }
      if (!isIntegerInRange(props.question_ordinal, 1, 5)) {
        recordRejection('invalid_question_ordinal');
        return { ok: false, reason: 'question_ordinal must be an integer between 1 and 5' };
      }
      break;
    }

    case 'reflection_interacted': {
      if (!isIntegerInRange(props.claim_ordinal, 1, 10)) {
        recordRejection('invalid_claim_ordinal');
        return { ok: false, reason: 'claim_ordinal must be an integer between 1 and 10' };
      }
      if (!isIntegerInRange(props.question_ordinal, 1, 5)) {
        recordRejection('invalid_question_ordinal');
        return { ok: false, reason: 'question_ordinal must be an integer between 1 and 5' };
      }
      const allowedInteractions = ['expanded', 'answered', 'dismissed'];
      if (typeof props.interaction !== 'string' || !allowedInteractions.includes(props.interaction)) {
        recordRejection('invalid_reflection_interaction');
        return { ok: false, reason: `Invalid reflection interaction: ${String(props.interaction)}` };
      }
      break;
    }

    case 'global_verdict_viewed': {
      // Empty object expected
      break;
    }

    case 'decision_submitted': {
      if (!isIntegerInRange(props.claim_ordinal, 1, 10)) {
        recordRejection('invalid_claim_ordinal');
        return { ok: false, reason: 'claim_ordinal must be an integer between 1 and 10' };
      }
      const allowedStages = ['pre_evidence', 'final'];
      if (typeof props.stage !== 'string' || !allowedStages.includes(props.stage)) {
        recordRejection('invalid_decision_stage');
        return { ok: false, reason: `Invalid stage: ${String(props.stage)}` };
      }
      const allowedVerdicts = ['supported', 'contradicted', 'misleading', 'insufficient', 'cannot_determine'];
      if (typeof props.decision !== 'string' || !allowedVerdicts.includes(props.decision)) {
        recordRejection('invalid_decision_verdict');
        return { ok: false, reason: `Invalid decision verdict: ${String(props.decision)}` };
      }
      if (!isIntegerInRange(props.confidence, 0, 100)) {
        recordRejection('invalid_confidence');
        return { ok: false, reason: 'confidence must be an integer between 0 and 100' };
      }
      break;
    }

    case 'post_task_questionnaire': {
      if (!isIntegerInRange(props.effort_seq, 1, 7)) {
        recordRejection('invalid_effort_seq');
        return { ok: false, reason: 'effort_seq must be an integer between 1 and 7' };
      }
      if (!Array.isArray(props.verification_steps) || props.verification_steps.length === 0) {
        recordRejection('invalid_verification_steps');
        return { ok: false, reason: 'verification_steps must be a non-empty array' };
      }
      const allowedSteps = new Set(['source', 'date', 'independent_evidence', 'context', 'none']);
      const seen = new Set<string>();
      for (const step of props.verification_steps) {
        if (typeof step !== 'string' || !allowedSteps.has(step)) {
          recordRejection('invalid_verification_step_value');
          return { ok: false, reason: `Invalid verification step: ${String(step)}` };
        }
        if (seen.has(step)) {
          recordRejection('duplicate_verification_step');
          return { ok: false, reason: `Duplicate verification step: ${step}` };
        }
        seen.add(step);
      }
      break;
    }

    case 'session_ended': {
      const allowedReasons = ['completed', 'abandoned', 'timeout'];
      if (typeof props.reason !== 'string' || !allowedReasons.includes(props.reason)) {
        recordRejection('invalid_session_end_reason');
        return { ok: false, reason: `Invalid end reason: ${String(props.reason)}` };
      }
      break;
    }
  }

  return { ok: true, event: raw as unknown as TelemetryEvent };
}
