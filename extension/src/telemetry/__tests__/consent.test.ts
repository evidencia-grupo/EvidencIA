import { describe, it, expect, beforeEach } from 'vitest';
import {
  setExperimentMode,
  grantConsent,
  revokeConsent,
  hasConsent,
  isExperimentMode,
  canEmitTelemetry,
  resetConsentState,
} from '../consent';
import { createSession } from '../session';
import { MemorySink } from '../sink';

describe('Consent & Experiment Mode Gate', () => {
  beforeEach(() => {
    resetConsentState();
  });

  const createSampleEvent = () => {
    const session = createSession({
      pid: 'P-0001',
      cond: 'B',
      phase: 'assisted',
      item_id: 'IT-001',
    });
    return session.createRawEvent('session_started', { build: '1a2b3c4' });
  };

  it('defaults to inactive for both experiment mode and participant consent', () => {
    expect(isExperimentMode()).toBe(false);
    expect(hasConsent()).toBe(false);
    expect(canEmitTelemetry()).toBe(false);
  });

  it('blocks recording when experiment mode is disabled even if consent is given', () => {
    grantConsent();
    expect(hasConsent()).toBe(true);
    expect(isExperimentMode()).toBe(false);
    expect(canEmitTelemetry()).toBe(false);

    const sink = new MemorySink();
    const recorded = sink.record(createSampleEvent());
    expect(recorded).toBe(false);
    expect(sink.count()).toBe(0);
  });

  it('blocks recording when experiment mode is enabled but consent is missing', () => {
    setExperimentMode(true);
    expect(isExperimentMode()).toBe(true);
    expect(hasConsent()).toBe(false);
    expect(canEmitTelemetry()).toBe(false);

    const sink = new MemorySink();
    const recorded = sink.record(createSampleEvent());
    expect(recorded).toBe(false);
    expect(sink.count()).toBe(0);
  });

  it('allows recording only when both experiment mode and consent are active', () => {
    setExperimentMode(true);
    grantConsent();
    expect(canEmitTelemetry()).toBe(true);

    const sink = new MemorySink();
    const ev = createSampleEvent();
    const recorded = sink.record(ev);
    expect(recorded).toBe(true);
    expect(sink.count()).toBe(1);
  });

  it('stops recording immediately when consent is revoked', () => {
    setExperimentMode(true);
    grantConsent();
    const sink = new MemorySink();

    expect(sink.record(createSampleEvent())).toBe(true);
    expect(sink.count()).toBe(1);

    revokeConsent();
    expect(hasConsent()).toBe(false);
    expect(canEmitTelemetry()).toBe(false);

    expect(sink.record(createSampleEvent())).toBe(false);
    expect(sink.count()).toBe(1); // No new event added
  });

  it('resets all consent state cleanly', () => {
    setExperimentMode(true);
    grantConsent();
    resetConsentState();

    expect(isExperimentMode()).toBe(false);
    expect(hasConsent()).toBe(false);
    expect(canEmitTelemetry()).toBe(false);
  });
});
