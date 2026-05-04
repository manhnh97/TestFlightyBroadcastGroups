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
