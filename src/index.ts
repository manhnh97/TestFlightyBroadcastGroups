import { BOTS } from './config';
import { handleUpdate, type TGUpdate } from './handlers';
import { BotStateDO } from './durable-objects';

export { BotStateDO };

export interface Env {
  // JSON map of bot_id -> bot token. Set via: wrangler secret put BOT_TOKENS
  BOT_TOKENS: string;
  // Durable Object binding for per-bot group + quota state
  BOT_STATE: DurableObjectNamespace<BotStateDO>;
}

const WEBHOOK_PATH = /^\/webhook\/([a-z0-9_-]+)$/i;

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === '/' || url.pathname === '/health') {
      return new Response(`OK\nBots: ${Object.keys(BOTS).join(', ')}\n`);
    }

    const m = url.pathname.match(WEBHOOK_PATH);
    if (!m) return new Response('Not found', { status: 404 });
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });

    const botId = m[1];
    const bot = BOTS[botId];
    if (!bot) return new Response('Unknown bot', { status: 404 });

    const tokens = parseTokens(env.BOT_TOKENS);
    const token = tokens[botId];
    if (!token) return new Response('Token not configured', { status: 500 });

    const update = (await request.json().catch(() => null)) as TGUpdate | null;
    if (!update) return new Response('Bad request', { status: 400 });

    const stub = env.BOT_STATE.get(env.BOT_STATE.idFromName(botId));

    // Respond 200 fast; let Telegram move on while we work.
    ctx.waitUntil(
      (async () => {
        if (bot.seedGroups?.length) await stub.ensureSeeded(bot.seedGroups);
        await stub.ensureDailyLimit(bot.dailyLimit);
        await handleUpdate(update, bot, token, stub);
      })().catch((e) => console.error(`[${botId}]`, e)),
    );
    return new Response('ok');
  },
};

function parseTokens(raw: string): Record<string, string> {
  try {
    return JSON.parse(raw) as Record<string, string>;
  } catch {
    return {};
  }
}
