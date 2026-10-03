import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { EVENT_ALLOWLIST, TelemetryEventName } from '../events';

describe('Schema Sync Validation', () => {
  it('ensures JSON Schema events and prop keys match EVENT_ALLOWLIST exactly', () => {
    const schemaPath = path.resolve(__dirname, '../schema/telemetry-event.schema.json');
    const rawSchema = fs.readFileSync(schemaPath, 'utf-8');
    const schema = JSON.parse(rawSchema);

    // 1. Check all events declared in schema.properties.event.enum
    const schemaEventEnum: string[] = schema.properties.event.enum;
    const tsEvents = Object.keys(EVENT_ALLOWLIST);

    expect(schemaEventEnum.sort()).toEqual(tsEvents.sort());

    // 2. Check each oneOf branch in schema
    const oneOfBranches = schema.oneOf as Array<{
      properties: {
        event: { const: string };
        props: {
          properties: Record<string, unknown>;
          required?: string[];
        };
      };
    }>;

    expect(oneOfBranches.length).toBe(tsEvents.length);

    for (const branch of oneOfBranches) {
      const eventName = branch.properties.event.const as TelemetryEventName;
      expect(eventName in EVENT_ALLOWLIST).toBe(true);

      const expectedProps = [...EVENT_ALLOWLIST[eventName]].sort();
      const actualSchemaProps = Object.keys(branch.properties.props.properties || {}).sort();

      expect(actualSchemaProps).toEqual(expectedProps);

      // Verify that all expected props are required (except for empty props like global_verdict_viewed)
      if (expectedProps.length > 0) {
        const requiredProps = [...(branch.properties.props.required || [])].sort();
        expect(requiredProps).toEqual(expectedProps);
      }
    }
  });
});
