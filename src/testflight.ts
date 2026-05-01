const URL_PATTERN_GLOBAL = /https?:\/\/[^\s)]*testflight\.apple\.com\/join\/[a-zA-Z0-9]{8}/g;
const URL_PATTERN = /https?:\/\/[^\s)]*testflight\.apple\.com\/join\/[a-zA-Z0-9]{8}/;
const TITLE_REGEX = /<title[^>]*>\s*Join the (.+?) beta - TestFlight - Apple\s*<\/title>/is;

const BROWSER_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15';

export function isTestFlightUrl(url: string): boolean {
  return URL_PATTERN.test(url);
}

export function extractTestFlightLinks(text: string): string[] {
  const matches = text.match(URL_PATTERN_GLOBAL) ?? [];
  return Array.from(new Set(matches));
}

export async function fetchAppName(url: string): Promise<string | null> {
  // Bust any cache on this fetch so we read the live title for every request.
  const r = await fetch(withNoCacheParam(url), { headers: { 'User-Agent': BROWSER_UA } });
  if (!r.ok) return null;
  const html = await r.text();
  const m = html.match(TITLE_REGEX);
  return m ? m[1].trim() : null;
}

// Preserve the original casing from the app name: "FV Transport" -> "#FV #Transport".
export function nameToHashtag(name: string): string {
  const words = name.match(/\b\w+\b/g) ?? [];
  return words.map((w) => '#' + w).join(' ');
}

// Cache-buster derived from unix time. Strips any existing query string first
// so the URL stays clean if the source already had params. The counter makes
// every call unique, even multiple calls within the same millisecond — so each
// per-group send in a broadcast gets its own nonce.
let nonceCounter = 0;

export function withNoCacheParam(url: string): string {
  const base = url.split('?')[0];
  const nonce = (Date.now() + nonceCounter++) % 10000;
  return `${base}?nocache=${nonce}`;
}
