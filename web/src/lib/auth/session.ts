// CineVault OS — Server-Side BFF Session Management
// Provides secure, encrypted/signed HttpOnly session cookie handling.
// Tokens are stored strictly server-side inside the session cookie and NEVER exposed to browser JS.

import crypto from "crypto";
import { cookies } from "next/headers";

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
const SESSION_SECRET = process.env.SESSION_SECRET || "cinevault-local-dev-session-secret-change-in-prod-32bytes!";

// Helper for AES-256-GCM encryption
function getSecretKey(): Buffer {
  return crypto.createHash("sha256").update(SESSION_SECRET).digest();
}

export function encryptSession(data: SessionData): string {
  const key = getSecretKey();
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  
  const jsonStr = JSON.stringify(data);
  let encrypted = cipher.update(jsonStr, "utf8", "base64");
  encrypted += cipher.final("base64");
  
  const authTag = cipher.getAuthTag();

  return `${iv.toString("base64")}.${authTag.toString("base64")}.${encrypted}`;
}

export function decryptSession(cookieValue: string): SessionData | null {
  try {
    const parts = cookieValue.split(".");
    if (parts.length !== 3) return null;

    const [ivB64, authTagB64, encryptedText] = parts;
    const key = getSecretKey();
    const iv = Buffer.from(ivB64, "base64");
    const authTag = Buffer.from(authTagB64, "base64");

    const decipher = crypto.createDecipheriv("aes-256-gcm", key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encryptedText, "base64", "utf8");
    decrypted += decipher.final("utf8");

    const session: SessionData = JSON.parse(decrypted);

    // Check expiration
    if (Date.now() >= session.expires_at) {
      return null;
    }

    return session;
  } catch {
    return null;
  }
}

export async function getSession(): Promise<SessionData | null> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME);

  if (!sessionCookie || !sessionCookie.value) {
    return null;
  }

  return decryptSession(sessionCookie.value);
}

export async function setSessionCookie(sessionData: SessionData): Promise<void> {
  const encrypted = encryptSession(sessionData);
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
