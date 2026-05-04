import { BOT } from './config';
import { handleUpdate, type TGUpdate } from './handlers';
import { BotStateDO } from './durable-objects';

export { BotStateDO };

export interface Env {
  // The bot token, set as a Secret in the dashboard. Plain string, not JSON.
  //   Variables and Secrets > Add > Type: Secret, Name: BOT_TOKENS,
  //   Value: 1234567890:AAE...
  BOT_TOKENS: string;

  // Optional comma-separated Telegram user ids to seed as admins on first
  // run. Lets the source repo stay clean of personal IDs. Set as a plaintext
  // Variable (or Secret) in the dashboard:
  //   Variables and Secrets > Add > Type: Plaintext, Name: SEED_ADMINS,
  //   Value: 123456789,987654321
  // If set, this overrides BOT.seedAdmins from src/config.ts.
  SEED_ADMINS?: string;

  // Durable Object binding for group + quota state.
  BOT_STATE: DurableObjectNamespace<BotStateDO>;
}

function parseAdminIds(s: string | undefined): number[] {
  if (!s) return [];
  return s
    .split(',')
    .map((x) => Number.parseInt(x.trim(), 10))
    .filter((n) => Number.isFinite(n) && n > 0);
}

const DO_NAME = 'bot';

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === '/' || url.pathname === '/health') {
      return new Response('OK\n');
    }

    if (url.pathname !== '/webhook') return new Response('Not found', { status: 404 });
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });

    const token = (env.BOT_TOKENS ?? '').trim();
    if (!token) return new Response('BOT_TOKENS not configured', { status: 500 });

    const update = (await request.json().catch(() => null)) as TGUpdate | null;
    if (!update) return new Response('Bad request', { status: 400 });

    const stub = env.BOT_STATE.get(env.BOT_STATE.idFromName(DO_NAME));

    // Respond 200 fast; let Telegram move on while we work.
    ctx.waitUntil(
      (async () => {
        if (BOT.seedGroups?.length) await stub.ensureSeeded(BOT.seedGroups);
        const envAdmins = parseAdminIds(env.SEED_ADMINS);
        const seedAdmins = envAdmins.length ? envAdmins : (BOT.seedAdmins ?? []);
        if (seedAdmins.length) await stub.ensureSeededAdmins(seedAdmins);
        await stub.ensureSeededDiscord(BOT.seedDiscordWebhook);
        await stub.ensureDailyLimit(BOT.dailyLimit);
        await handleUpdate(update, BOT, token, stub);
      })().catch(async (e) => {
        console.error('handler error:', e);
        // Surface the failure back to the user so it stops looking like a silent no-op.
        const chatId = update.message?.chat?.id;
        if (chatId) {
          await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              chat_id: chatId,
              text: `internal error: ${(e as Error).message ?? String(e)}`,
            }),
          }).catch(() => {});
        }
      }),
    );
    return new Response('ok');
  },
};
