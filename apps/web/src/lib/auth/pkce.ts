// CineVault OS — PKCE (Proof Key for Code Exchange) Utility (RFC 7636)
// Provides cryptographically secure code_verifier and S256 code_challenge generation.

import crypto from "crypto";

function base64UrlEncode(buffer: Buffer): string {
  return buffer
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

export function generateCodeVerifier(): string {
  // Generate 32 random bytes -> 43 base64url characters
  const randomBytes = crypto.randomBytes(32);
  return base64UrlEncode(randomBytes);
}

export function generateCodeChallenge(verifier: string): string {
  const hash = crypto.createHash("sha256").update(verifier).digest();
  return base64UrlEncode(hash);
}

export function generateState(): string {
  return base64UrlEncode(crypto.randomBytes(16));
}
