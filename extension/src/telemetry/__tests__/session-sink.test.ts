import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as TelemetryIndex from '../index';
import {
  createSession,
  MemorySink,
  ChromeStorageSink,
  toJsonl,
  setExperimentMode,
  grantConsent,
  resetConsentState,
} from '../index';

describe('Telemetry Session & Sink Suite', () => {
  beforeEach(() => {
    resetConsentState();
  });

  it('exports all expected members from index.ts', () => {
    expect(TelemetryIndex.createSession).toBeDefined();
    expect(TelemetryIndex.MemorySink).toBeDefined();
    expect(TelemetryIndex.validateEvent).toBeDefined();
    expect(TelemetryIndex.grantConsent).toBeDefined();
  });

  describe('createSession', () => {
    it('initializes session with correct properties and monotonic sequences', () => {
      const session = createSession({
        pid: 'P-0002',
        cond: 'B',
        phase: 'assisted',
        item_id: 'IT-002',
      });

      expect(session.getPid()).toBe('P-0002');
      expect(session.getCondition()).toBe('B');
      expect(session.getPhase()).toBe('assisted');
      expect(session.getItemId()).toBe('IT-002');
      expect(session.getSid()).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
      expect(session.getSequence()).toBe(0);

      const ev1 = session.createRawEvent('item_presented', { n_claims: 2 });
      expect(ev1.seq).toBe(0);
      expect(session.getSequence()).toBe(1);

      const ev2 = session.createRawEvent('claim_selected', { claim_ordinal: 1 });
      expect(ev2.seq).toBe(1);
      expect(session.getSequence()).toBe(2);
    });

    it('updates phase and item_id correctly', () => {
      const session = createSession({
        pid: 'P-0003',
        cond: 'A',
        phase: 'baseline',
        item_id: 'IT-001',
      });

      session.setPhase('assisted');
      expect(session.getPhase()).toBe('assisted');

      session.setItemId('IT-003');
      expect(session.getItemId()).toBe('IT-003');

      expect(() => session.setPhase('invalid' as any)).toThrow();
      expect(() => session.setItemId('INVALID')).toThrow();
    });

    it('validates initial config and throws on invalid inputs', () => {
      expect(() => createSession({ pid: 'invalid', cond: 'A', phase: 'baseline', item_id: 'IT-001' })).toThrow();
      expect(() => createSession({ pid: 'P-0001', cond: 'C' as any, phase: 'baseline', item_id: 'IT-001' })).toThrow();
      expect(() => createSession({ pid: 'P-0001', cond: 'A', phase: 'invalid' as any, item_id: 'IT-001' })).toThrow();
      expect(() => createSession({ pid: 'P-0001', cond: 'A', phase: 'baseline', item_id: 'invalid' })).toThrow();
    });
  });

  describe('MemorySink and toJsonl', () => {
    it('buffers events and exports them to clean JSONL', () => {
      setExperimentMode(true);
      grantConsent();

      const session = createSession({
        pid: 'P-0001',
        cond: 'B',
        phase: 'assisted',
        item_id: 'IT-001',
      });

      const sink = new MemorySink();
      const ev1 = session.createRawEvent('session_started', { build: '1a2b3c4' });
      const ev2 = session.createRawEvent('item_presented', { n_claims: 3 });

      expect(sink.record(ev1)).toBe(true);
      expect(sink.record(ev2)).toBe(true);
      expect(sink.count()).toBe(2);
      expect(sink.getEvents()).toHaveLength(2);

      const jsonl = sink.exportJsonl();
      const lines = jsonl.trim().split('\n');
      expect(lines).toHaveLength(2);

      const parsed1 = JSON.parse(lines[0]);
      expect(parsed1.event).toBe('session_started');
      expect(parsed1.props.build).toBe('1a2b3c4');

      sink.clear();
      expect(sink.count()).toBe(0);
      expect(sink.exportJsonl()).toBe('');
    });

    it('returns empty string for empty event list in toJsonl', () => {
      expect(toJsonl([])).toBe('');
    });
  });

  describe('ChromeStorageSink', () => {
    it('handles persistence fallback gracefully when chrome storage is not present in mock env', async () => {
      const sink = new ChromeStorageSink('test_key');
      const resSet = await sink.persistToChromeStorage();
      const resGet = await sink.loadFromChromeStorage();
      expect(typeof resSet).toBe('boolean');
      expect(typeof resGet).toBe('boolean');
    });

    it('persists and loads from chrome.storage.local when available', async () => {
      setExperimentMode(true);
      grantConsent();

      let storedData: Record<string, string> = {};
      (globalThis as any).chrome = {
        storage: {
          local: {
            set: vi.fn(async (obj: Record<string, string>) => {
              storedData = { ...storedData, ...obj };
            }),
            get: vi.fn(async (key: string) => {
              return { [key]: storedData[key] };
            }),
          },
        },
      };

      const session = createSession({
        pid: 'P-0001',
        cond: 'B',
        phase: 'assisted',
        item_id: 'IT-001',
      });
      const sink = new ChromeStorageSink('test_act_key');
      const ev = session.createRawEvent('session_started', { build: '1a2b3c4' });
      sink.record(ev);

      const saved = await sink.persistToChromeStorage();
      expect(saved).toBe(true);

      const newSink = new ChromeStorageSink('test_act_key');
      const loaded = await newSink.loadFromChromeStorage();
      expect(loaded).toBe(true);
      expect(newSink.count()).toBe(1);

      delete (globalThis as any).chrome;
    });

    it('handles chrome.storage errors gracefully', async () => {
      (globalThis as any).chrome = {
        storage: {
          local: {
            set: vi.fn().mockRejectedValue(new Error('Storage quota exceeded')),
            get: vi.fn().mockRejectedValue(new Error('Storage failure')),
          },
        },
      };

      const sink = new ChromeStorageSink('error_key');
      expect(await sink.persistToChromeStorage()).toBe(false);
      expect(await sink.loadFromChromeStorage()).toBe(false);

      delete (globalThis as any).chrome;
    });
  });
});
