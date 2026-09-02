// CineVault OS — Universal BFF Session Management
// Uses standard Web Crypto API (AES-GCM 256-bit + SHA-256 key derivation)
// 100% compatible across Next.js Edge Runtime (Middleware) and Node.js Runtime.

export interface SessionUser {
  sub: string;
  email?: string;
  username?: string;
  roles: string[];
}

export interface SessionData {
  access_token: string;
  refresh_token?: string;
  user: SessionUser;
  expires_at: number;
}

export const SESSION_COOKIE_NAME = "cinevault_session";

const INSECURE_DEFAULT_SESSION_SECRET = "cinevault-local-dev-session-secret-change-in-prod-32bytes!";

// instrumentation.ts already refuses to boot the production server when
// SESSION_SECRET is unset — this second check is defense-in-depth at the
// actual point of use, so this function itself never silently signs a
// production session with the public dev default even if some future code
// path calls it before/outside that startup hook.
function getSecret(): string {
  const secret = process.env.SESSION_SECRET;
  if (secret) return secret;

  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "SESSION_SECRET is not set — refusing to sign/verify a session cookie in production " +
        "with the insecure development default."
    );
  }

  return INSECURE_DEFAULT_SESSION_SECRET;
}

function uint8ArrayToBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function base64UrlToUint8Array(base64url: string): Uint8Array {
  let base64 = base64url.replace(/-/g, "+").replace(/_/g, "/");
  while (base64.length % 4) {
    base64 += "=";
  }
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function getCryptoKey(): Promise<CryptoKey> {
  const secret = getSecret();
  const encoder = new TextEncoder();
  const keyHash = await crypto.subtle.digest("SHA-256", encoder.encode(secret));
  return crypto.subtle.importKey("raw", keyHash, { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
}

export async function encryptSession(data: SessionData): Promise<string> {
  const cryptoKey = await getCryptoKey();
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoder = new TextEncoder();
  const dataBytes = encoder.encode(JSON.stringify(data));

  const encryptedBuf = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: iv as unknown as BufferSource },
    cryptoKey,
    dataBytes as unknown as BufferSource
  );

  const ivB64 = uint8ArrayToBase64Url(iv);
  const encB64 = uint8ArrayToBase64Url(new Uint8Array(encryptedBuf));

  return `${ivB64}.${encB64}`;
}

export async function decryptSessionUnchecked(cookieValue: string): Promise<SessionData | null> {
  try {
    if (!cookieValue) return null;
    const rawValue = cookieValue.includes("%") ? decodeURIComponent(cookieValue) : cookieValue;
    const parts = rawValue.split(".");
    if (parts.length !== 2) return null;

    const [ivB64, encB64] = parts;
    const iv = base64UrlToUint8Array(ivB64);
    const encBytes = base64UrlToUint8Array(encB64);

    const cryptoKey = await getCryptoKey();
    const decryptedBuf = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: iv as unknown as BufferSource },
      cryptoKey,
      encBytes as unknown as BufferSource
    );

    const decoder = new TextDecoder();
    const jsonStr = decoder.decode(decryptedBuf);
    return JSON.parse(jsonStr) as SessionData;
  } catch {
    return null;
  }
}

export async function decryptSession(cookieValue: string): Promise<SessionData | null> {
  const session = await decryptSessionUnchecked(cookieValue);
  if (!session) return null;

  if (Date.now() >= session.expires_at) {
    return null;
  }

  return session;
}

import { cookies } from "next/headers";

export async function getSession(): Promise<SessionData | null> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);

  if (!sessionCookie || !sessionCookie.value) {
    return null;
  }

  return decryptSession(sessionCookie.value);
}

export async function setSessionCookie(sessionData: SessionData): Promise<void> {
  const encrypted = await encryptSession(sessionData);
  const cookieStore = await cookies();

  cookieStore.set(SESSION_COOKIE_NAME, encrypted, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    expires: new Date(sessionData.expires_at),
  });
}

export async function clearSessionCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE_NAME);
}
