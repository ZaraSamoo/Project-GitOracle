"use client";

const USER_ID_KEY = "internhub_user_id";
const AUTH_TOKEN_KEY = "internhub_auth_token";

export function getSessionUserId(): number | null {
  if (typeof window === "undefined") {
    return null;
  }

  const stored = window.localStorage.getItem(USER_ID_KEY);
  if (!stored) {
    return null;
  }

  const parsed = Number.parseInt(stored, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return null;
  }
  return parsed;
}

export function setSessionUserId(userId: number): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(USER_ID_KEY, String(userId));
}

export function getSessionToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setSessionToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
}
