const CLIENT_DEFAULT_FLASK_BASE_URL = "/flask";
const SERVER_DEFAULT_FLASK_BASE_URL = "http://127.0.0.1:5000";

const CLIENT_FLASK_BASE_URL =
  process.env.NEXT_PUBLIC_FLASK_API_BASE?.trim() || CLIENT_DEFAULT_FLASK_BASE_URL;
const SERVER_FLASK_BASE_URL =
  process.env.FLASK_API_BASE?.trim() || SERVER_DEFAULT_FLASK_BASE_URL;

type ApiRequestOptions = RequestInit & {
  path: string;
};

export async function flaskRequest<T>({ path, ...init }: ApiRequestOptions): Promise<T> {
  const baseUrl = typeof window === "undefined" ? SERVER_FLASK_BASE_URL : CLIENT_FLASK_BASE_URL;
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(
      `Flask request failed: ${response.status} ${response.statusText}${body ? ` - ${body}` : ""}`
    );
  }

  return (await response.json()) as T;
}
