/**
 * Telemetry session manager.
 * Generates UUID v4 session IDs, relative millisecond offsets (t_ms) and monotonic sequences.
 */

import {
  ITEM_ID_REGEX,
  PID_REGEX,
  TelemetryCondition,
  TelemetryEventName,
  TelemetryPhase,
  TelemetryPropsMap,
  BaseTelemetryEnvelope,
} from './events';

export interface SessionConfig {
  pid: string;
  cond: TelemetryCondition;
  phase: TelemetryPhase;
  item_id: string;
  sid?: string;
  startTime?: number;
}

export interface TelemetrySession {
  getPid(): string;
  getSid(): string;
  getCondition(): TelemetryCondition;
  getPhase(): TelemetryPhase;
  getItemId(): string;
  getSequence(): number;
  setPhase(phase: TelemetryPhase): void;
  setItemId(itemId: string): void;
  createRawEvent<E extends TelemetryEventName>(event: E, props: TelemetryPropsMap[E]): BaseTelemetryEnvelope<E>;
}

function generateUuidV4(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Standard RFC4122 compliant fallback
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getPerformanceNow(): number {
  if (typeof performance !== 'undefined' && typeof performance.now === 'function') {
    return performance.now();
  }
  return Date.now();
}

export function createSession(config: SessionConfig): TelemetrySession {
  if (!PID_REGEX.test(config.pid)) {
    throw new Error(`Invalid pid: expected format ^P-[0-9]{4}$, got "${config.pid}"`);
  }
  if (!ITEM_ID_REGEX.test(config.item_id)) {
    throw new Error(`Invalid item_id: expected format ^IT-[0-9]{3}$, got "${config.item_id}"`);
  }
  if (config.cond !== 'A' && config.cond !== 'B') {
    throw new Error(`Invalid condition: expected "A" or "B", got "${config.cond}"`);
  }
  if (config.phase !== 'baseline' && config.phase !== 'assisted' && config.phase !== 'transfer') {
    throw new Error(`Invalid phase: got "${config.phase}"`);
  }

  const pid = config.pid;
  const sid = config.sid || generateUuidV4();
  const cond = config.cond;
  let phase = config.phase;
  let itemId = config.item_id;

  const sessionStartPerf = config.startTime ?? getPerformanceNow();
  let seqCounter = 0;

  return {
    getPid: () => pid,
    getSid: () => sid,
    getCondition: () => cond,
    getPhase: () => phase,
    getItemId: () => itemId,
    getSequence: () => seqCounter,
    setPhase: (newPhase: TelemetryPhase) => {
      if (newPhase !== 'baseline' && newPhase !== 'assisted' && newPhase !== 'transfer') {
        throw new Error(`Invalid phase: "${newPhase}"`);
      }
      phase = newPhase;
    },
    setItemId: (newItemId: string) => {
      if (!ITEM_ID_REGEX.test(newItemId)) {
        throw new Error(`Invalid item_id: "${newItemId}"`);
      }
      itemId = newItemId;
    },
    createRawEvent<E extends TelemetryEventName>(event: E, props: TelemetryPropsMap[E]): BaseTelemetryEnvelope<E> {
      const currentPerf = getPerformanceNow();
      const deltaMs = Math.max(0, Math.round(currentPerf - sessionStartPerf));
      const currentSeq = seqCounter++;

      return {
        schema_version: '1.0.0',
        pid,
        sid,
        cond,
        phase,
        item_id: itemId,
        event,
        seq: currentSeq,
        t_ms: deltaMs,
        props,
      };
    },
  };
}
