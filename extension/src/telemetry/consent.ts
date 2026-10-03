/**
 * Double-gate consent and experiment mode manager for CBL Act telemetry.
 * Strict privacy: in-memory state only, no persistence across sessions, default off.
 */

// Build-time constant flag (defaults to false in production builds)
let experimentModeActive = false;

// Transient in-memory consent gate
let participantConsentGranted = false;

export function setExperimentMode(active: boolean): void {
  experimentModeActive = active;
}

export function isExperimentMode(): boolean {
  return experimentModeActive;
}

export function grantConsent(): void {
  participantConsentGranted = true;
}

export function revokeConsent(): void {
  participantConsentGranted = false;
}

export function hasConsent(): boolean {
  return participantConsentGranted;
}

/**
 * Both experiment build mode and participant consent must be strictly active
 * for any telemetry event to be recorded or exported.
 */
export function canEmitTelemetry(): boolean {
  return experimentModeActive && participantConsentGranted;
}

export function resetConsentState(): void {
  experimentModeActive = false;
  participantConsentGranted = false;
}
