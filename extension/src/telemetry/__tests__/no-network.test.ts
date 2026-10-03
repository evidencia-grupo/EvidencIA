import { describe, it, expect } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';

describe('No-Network Architecture Invariant', () => {
  const forbiddenPatterns = [
    { name: 'fetch()', regex: /\bfetch\s*\(/ },
    { name: 'XMLHttpRequest', regex: /\bXMLHttpRequest\b/ },
    { name: 'navigator.sendBeacon', regex: /\bsendBeacon\s*\(/ },
    { name: 'WebSocket', regex: /\bWebSocket\b/ },
    { name: 'EventSource', regex: /\bEventSource\b/ },
    { name: 'remote dynamic import', regex: /\bimport\s*\(\s*['"`]https?:\/\// },
  ];

  it('scans all telemetry source files and asserts 0 network or transmission calls', () => {
    const telemetryDir = path.resolve(__dirname, '..');
    const files = fs.readdirSync(telemetryDir);

    const violations: string[] = [];

    for (const file of files) {
      const fullPath = path.join(telemetryDir, file);
      const stat = fs.statSync(fullPath);

      if (stat.isFile() && file.endsWith('.ts') && !file.endsWith('.test.ts')) {
        const content = fs.readFileSync(fullPath, 'utf-8');

        for (const pattern of forbiddenPatterns) {
          if (pattern.regex.test(content)) {
            violations.push(`File ${file} contains forbidden network call: ${pattern.name}`);
          }
        }
      }
    }

    expect(violations).toEqual([]);
  });
});
