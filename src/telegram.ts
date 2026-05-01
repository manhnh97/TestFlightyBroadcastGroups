export type SendMessageParams = {
  chat_id: string | number;
  text: string;
  message_thread_id?: number;
  parse_mode?: 'Markdown' | 'MarkdownV2' | 'HTML';
  disable_web_page_preview?: boolean;
  reply_parameters?: { message_id: number };
};

export async function sendMessage(token: string, params: SendMessageParams): Promise<Response> {
  return fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

export async function sendDiscord(webhook: string, content: string): Promise<Response> {
  return fetch(webhook, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
}

export type ChatInfo = {
  id: number;
  type: 'private' | 'group' | 'supergroup' | 'channel';
  title?: string;
  username?: string;
};

// Look up chat info by @username (or numeric id). Returns null if Telegram
// doesn't know the chat, the bot can't access it, or the chat is private
// (non-public usernames cannot be resolved this way).
export async function getChat(token: string, chatRef: string): Promise<ChatInfo | null> {
  const r = await fetch(
    `https://api.telegram.org/bot${token}/getChat?chat_id=${encodeURIComponent(chatRef)}`,
  );
  const data = (await r.json().catch(() => null)) as
    | { ok: boolean; result?: ChatInfo; description?: string }
    | null;
  return data?.ok ? data.result ?? null : null;
}
