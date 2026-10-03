import { describe, it, expect, beforeEach } from 'vitest';
import {
  validateEvent,
  getRejectionStats,
  resetRejectionStats,
} from '../sanitize';
import { TelemetryEventName } from '../events';

describe('Telemetry Sanitizer (Fail-Closed)', () => {
  beforeEach(() => {
    resetRejectionStats();
  });

  const validBaseEnvelope = {
    schema_version: '1.0.0',
    pid: 'P-0001',
    sid: '12345678-1234-4234-8234-123456789abc',
    cond: 'B',
    phase: 'assisted',
    item_id: 'IT-001',
    seq: 0,
    t_ms: 1500,
  };

  const samplePropsPerEvent: Record<TelemetryEventName, Record<string, unknown>> = {
    session_started: { build: '1a2b3c4' },
    item_presented: { n_claims: 3 },
    claims_viewed: { n_claims_visible: 3 },
    claim_selected: { claim_ordinal: 1 },
    evidence_expanded: { claim_ordinal: 1, evidence_ordinal: 1, relation: 'supports' },
    source_opened: { claim_ordinal: 1, evidence_ordinal: 1 },
    uncertainty_viewed: { claim_ordinal: 1, kind: 'insufficient_evidence' },
    reflection_viewed: { claim_ordinal: 1, question_ordinal: 1 },
    reflection_interacted: { claim_ordinal: 1, question_ordinal: 1, interaction: 'expanded' },
    global_verdict_viewed: {},
    decision_submitted: { claim_ordinal: 1, stage: 'final', decision: 'supported', confidence: 85 },
    post_task_questionnaire: { effort_seq: 5, verification_steps: ['source', 'context'] },
    session_ended: { reason: 'completed' },
  };

  it('accepts valid events for every defined event type', () => {
    for (const [eventName, props] of Object.entries(samplePropsPerEvent)) {
      const raw = {
        ...validBaseEnvelope,
        event: eventName,
        props,
      };
      const res = validateEvent(raw);
      expect(res.ok).toBe(true);
      if (res.ok) {
        expect(res.event.event).toBe(eventName);
      }
    }
  });

  it('accepts event with optional synthetic: true', () => {
    const raw = {
      ...validBaseEnvelope,
      event: 'session_started',
      synthetic: true,
      props: { build: '1a2b3c4' },
    };
    expect(validateEvent(raw).ok).toBe(true);
  });

  it('rejects events with extra keys in envelope', () => {
    const raw = {
      ...validBaseEnvelope,
      event: 'session_started',
      props: { build: '1a2b3c4' },
      injected_metadata: 'malicious',
    };
    const res = validateEvent(raw);
    expect(res.ok).toBe(false);
    expect(getRejectionStats()['unknown_envelope_key']).toBeGreaterThanOrEqual(1);
  });

  it('rejects events with extra keys in props', () => {
    const raw = {
      ...validBaseEnvelope,
      event: 'item_presented',
      props: {
        n_claims: 2,
        extra_note: 'not allowed',
      },
    };
    const res = validateEvent(raw);
    expect(res.ok).toBe(false);
  });

  it('rejects events with missing keys in envelope', () => {
    const raw: Record<string, unknown> = {
      schema_version: '1.0.0',
      pid: 'P-0001',
      // sid is missing
      cond: 'B',
      phase: 'assisted',
      item_id: 'IT-001',
      event: 'session_started',
      seq: 0,
      t_ms: 10,
      props: { build: '1a2b3c4' },
    };
    const res = validateEvent(raw);
    expect(res.ok).toBe(false);
    expect(getRejectionStats()['missing_envelope_key']).toBeGreaterThanOrEqual(1);
  });

  it('rejects invalid schema_version, pid, sid, cond, phase, item_id, event, seq, t_ms', () => {
    expect(validateEvent({ ...validBaseEnvelope, schema_version: '2.0.0', event: 'session_started', props: { build: '1a2b3c4' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, pid: 'INVALID', event: 'session_started', props: { build: '1a2b3c4' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, sid: 'not-a-uuid', event: 'session_started', props: { build: '1a2b3c4' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, cond: 'C', event: 'session_started', props: { build: '1a2b3c4' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, phase: 'unknown', event: 'session_started', props: { build: '1a2b3c4' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, item_id: 'INVALID', event: 'session_started', props: { build: '1a2b3c4' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'unknown_event', props: {} }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, seq: -1, event: 'session_started', props: { build: '1a2b3c4' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, t_ms: -10, event: 'session_started', props: { build: '1a2b3c4' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'session_started', props: 'not-an-object' }).ok).toBe(false);
    expect(validateEvent(null).ok).toBe(false);
  });

  it('rejects URL strings in props', () => {
    const raw = {
      ...validBaseEnvelope,
      event: 'session_started',
      props: { build: 'https://evil.com/hash' },
    };
    const res = validateEvent(raw);
    expect(res.ok).toBe(false);
    expect(getRejectionStats()['invalid_build_hash']).toBeGreaterThanOrEqual(1);
  });

  it('rejects email addresses in props', () => {
    const raw = {
      ...validBaseEnvelope,
      event: 'session_started',
      props: { build: 'user@example.com' },
    };
    const res = validateEvent(raw);
    expect(res.ok).toBe(false);
  });

  it('rejects CPF patterns in props', () => {
    const raw = {
      ...validBaseEnvelope,
      event: 'session_started',
      props: { build: '123.456.789-00' },
    };
    const res = validateEvent(raw);
    expect(res.ok).toBe(false);
  });

  it('rejects strings longer than 64 characters (transcription protection)', () => {
    const longString = 'a'.repeat(65);
    const raw = {
      ...validBaseEnvelope,
      event: 'session_started',
      props: { build: longString },
    };
    const res = validateEvent(raw);
    expect(res.ok).toBe(false);
  });

  it('rejects invalid props per specific event', () => {
    // item_presented
    expect(validateEvent({ ...validBaseEnvelope, event: 'item_presented', props: { n_claims: 15 } }).ok).toBe(false);
    // claims_viewed
    expect(validateEvent({ ...validBaseEnvelope, event: 'claims_viewed', props: { n_claims_visible: 0 } }).ok).toBe(false);
    // claim_selected
    expect(validateEvent({ ...validBaseEnvelope, event: 'claim_selected', props: { claim_ordinal: 11 } }).ok).toBe(false);
    // evidence_expanded
    expect(validateEvent({ ...validBaseEnvelope, event: 'evidence_expanded', props: { claim_ordinal: 0, evidence_ordinal: 1, relation: 'supports' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'evidence_expanded', props: { claim_ordinal: 1, evidence_ordinal: 25, relation: 'supports' } }).ok).toBe(false);
    // source_opened
    expect(validateEvent({ ...validBaseEnvelope, event: 'source_opened', props: { claim_ordinal: 0, evidence_ordinal: 1 } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'source_opened', props: { claim_ordinal: 1, evidence_ordinal: 25 } }).ok).toBe(false);
    // uncertainty_viewed
    expect(validateEvent({ ...validBaseEnvelope, event: 'uncertainty_viewed', props: { claim_ordinal: 0, kind: 'conflicting' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'uncertainty_viewed', props: { claim_ordinal: 1, kind: 'unknown_kind' } }).ok).toBe(false);
    // reflection_viewed
    expect(validateEvent({ ...validBaseEnvelope, event: 'reflection_viewed', props: { claim_ordinal: 0, question_ordinal: 1 } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'reflection_viewed', props: { claim_ordinal: 1, question_ordinal: 6 } }).ok).toBe(false);
    // reflection_interacted
    expect(validateEvent({ ...validBaseEnvelope, event: 'reflection_interacted', props: { claim_ordinal: 0, question_ordinal: 1, interaction: 'expanded' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'reflection_interacted', props: { claim_ordinal: 1, question_ordinal: 6, interaction: 'expanded' } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'reflection_interacted', props: { claim_ordinal: 1, question_ordinal: 1, interaction: 'clicked' } }).ok).toBe(false);
    // decision_submitted
    expect(validateEvent({ ...validBaseEnvelope, event: 'decision_submitted', props: { claim_ordinal: 0, stage: 'final', decision: 'supported', confidence: 50 } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'decision_submitted', props: { claim_ordinal: 1, stage: 'midway', decision: 'supported', confidence: 50 } }).ok).toBe(false);
    // post_task_questionnaire
    expect(validateEvent({ ...validBaseEnvelope, event: 'post_task_questionnaire', props: { effort_seq: 5, verification_steps: [] } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'post_task_questionnaire', props: { effort_seq: 5, verification_steps: ['invalid_step'] } }).ok).toBe(false);
    expect(validateEvent({ ...validBaseEnvelope, event: 'post_task_questionnaire', props: { effort_seq: 5, verification_steps: ['source', 'source'] } }).ok).toBe(false);
    // session_ended
    expect(validateEvent({ ...validBaseEnvelope, event: 'session_ended', props: { reason: 'crashed' } }).ok).toBe(false);
  });

  it('rejects confidence > 100 or < 0', () => {
    const raw101 = {
      ...validBaseEnvelope,
      event: 'decision_submitted',
      props: { claim_ordinal: 1, stage: 'final', decision: 'supported', confidence: 101 },
    };
    expect(validateEvent(raw101).ok).toBe(false);

    const rawNegative = {
      ...validBaseEnvelope,
      event: 'decision_submitted',
      props: { claim_ordinal: 1, stage: 'final', decision: 'supported', confidence: -1 },
    };
    expect(validateEvent(rawNegative).ok).toBe(false);
  });

  it('rejects effort_seq out of bounds (1..7)', () => {
    const rawZero = {
      ...validBaseEnvelope,
      event: 'post_task_questionnaire',
      props: { effort_seq: 0, verification_steps: ['source'] },
    };
    expect(validateEvent(rawZero).ok).toBe(false);

    const rawEight = {
      ...validBaseEnvelope,
      event: 'post_task_questionnaire',
      props: { effort_seq: 8, verification_steps: ['source'] },
    };
    expect(validateEvent(rawEight).ok).toBe(false);
  });

  it('rejects invalid enums in relation, kind, stage and decision', () => {
    const rawRelation = {
      ...validBaseEnvelope,
      event: 'evidence_expanded',
      props: { claim_ordinal: 1, evidence_ordinal: 1, relation: 'truthful' }, // invalid enum
    };
    expect(validateEvent(rawRelation).ok).toBe(false);

    const rawDecision = {
      ...validBaseEnvelope,
      event: 'decision_submitted',
      props: { claim_ordinal: 1, stage: 'final', decision: 'fake_news', confidence: 50 }, // invalid enum
    };
    expect(validateEvent(rawDecision).ok).toBe(false);
  });

  it('rejects forbidden keys such as "text", "transcript", "url"', () => {
    const rawForbidden = {
      ...validBaseEnvelope,
      event: 'session_started',
      props: { build: '1a2b3c4', transcript: 'video content text' },
    };
    expect(validateEvent(rawForbidden).ok).toBe(false);
    expect(getRejectionStats()['forbidden_key_in_props']).toBeGreaterThanOrEqual(1);
  });

  it('never mutates input object to fix it', () => {
    const originalInput = Object.freeze({
      ...validBaseEnvelope,
      event: 'session_started',
      props: Object.freeze({ build: 'INVALID_BUILD!' }),
    });

    const res = validateEvent(originalInput);
    expect(res.ok).toBe(false);
    expect(originalInput.props.build).toBe('INVALID_BUILD!');
  });
});
