/**
 * Telemetry sink interfaces and in-memory implementation.
 * Provides JSONL serialization and local buffering without network access.
 */

import { canEmitTelemetry } from './consent';
import { TelemetryEvent } from './events';
import { recordRejection, validateEvent } from './sanitize';

export interface TelemetrySink {
  record(rawEvent: unknown): boolean;
  getEvents(): TelemetryEvent[];
  count(): number;
  clear(): void;
  exportJsonl(): string;
}

/**
 * Pure function to serialize telemetry events into strict newline-delimited JSON (JSONL).
 */
export function toJsonl(events: readonly TelemetryEvent[]): string {
  if (events.length === 0) return '';
  return events.map((ev) => JSON.stringify(ev)).join('\n') + '\n';
}

/**
 * In-memory telemetry sink for safe session buffering.
 * Strictly adheres to double-gate consent check and fail-closed validation.
 */
export class MemorySink implements TelemetrySink {
  private buffer: TelemetryEvent[] = [];

  public record(rawEvent: unknown): boolean {
    // 1. Consent and Experiment mode gate
    if (!canEmitTelemetry()) {
      recordRejection('consent_or_experiment_mode_inactive');
      return false;
    }

    // 2. Strict sanitization and validation
    const result = validateEvent(rawEvent);
    if (!result.ok) {
      return false;
    }

    this.buffer.push(result.event);
    return true;
  }

  public getEvents(): TelemetryEvent[] {
    return [...this.buffer];
  }

  public count(): number {
    return this.buffer.length;
  }

  public clear(): void {
    this.buffer = [];
  }

  public exportJsonl(): string {
    return toJsonl(this.buffer);
  }
}

/**
 * Optional local storage sink using chrome.storage.local (as permission is declared).
 * Operates purely offline without any remote network dispatch.
 */
export class ChromeStorageSink extends MemorySink {
  private storageKey: string;

  constructor(storageKey = 'evidencia_act_telemetry') {
    super();
    this.storageKey = storageKey;
  }

  public async persistToChromeStorage(): Promise<boolean> {
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      try {
        const payload = this.exportJsonl();
        await chrome.storage.local.set({ [this.storageKey]: payload });
        return true;
      } catch {
        return false;
      }
    }
    return false;
  }

  public async loadFromChromeStorage(): Promise<boolean> {
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      try {
        const data = await chrome.storage.local.get(this.storageKey);
        const raw = data[this.storageKey];
        if (typeof raw === 'string') {
          const lines = raw.trim().split('\n');
          this.clear();
          for (const line of lines) {
            if (!line) continue;
            const parsed = JSON.parse(line);
            this.record(parsed);
          }
          return true;
        }
      } catch {
        return false;
      }
    }
    return false;
  }
}
