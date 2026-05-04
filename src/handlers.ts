import type { BotConfig } from './config';
import type { BotStateDO } from './durable-objects';
import { sendMessage, sendDiscord } from './telegram';
import {
  extractTestFlightLinks,
  fetchAppName,
  isTestFlightUrl,
  nameToHashtag,
} from './testflight';

type TGUser = { id: number; first_name?: string; username?: string; is_bot?: boolean };
type TGEntity = { type: string; offset: number; length: number; url?: string };
type TGMessage = {
  message_id: number;
  from?: TGUser;
  chat: { id: number; type: string; title?: string };
  text?: string;
  entities?: TGEntity[];
};
export type TGUpdate = { update_id: number; message?: TGMessage };

type State = DurableObjectStub<BotStateDO>;

export async function handleUpdate(
  update: TGUpdate,
  bot: BotConfig,
  token: string,
  state: State,
): Promise<void> {
  const msg = update.message;
  if (!msg || !msg.from || msg.from.is_bot) return;

  const isPrivate = msg.chat.type === 'private';
  const text = msg.text ?? '';

  if (!isPrivate) return;

  const admins = await state.listAdmins();
  const isAdmin = admins.includes(msg.from.id);

  // Every accepted webhook update consumes 1 quota slot. When the daily
  // budget is exhausted, drop silently for non-admins; for admins, send one
  // last notification per dropped request so they know to stop or /setlimit.
  const consume = await state.tryConsume();
  if (!consume.ok) {
    if (isAdmin) {
      await sendMessage(token, {
        chat_id: msg.chat.id.toString(),
        text:
          `quota ${consume.count}/${consume.limit} reached for today (VN). ` +
          `request dropped. resets at 00:00 VN, or raise it with /setlimit N.`,
      });
    }
    return;
  }

  if (text.startsWith('/')) {
    await handleCommand(msg, bot, token, state, isAdmin);
    return;
  }

  if (!isAdmin) return;

  const urls = collectTestFlightUrls(msg);
  const sharedBy = bot.sharedBy ?? msg.from.first_name ?? 'Anonymous';
  for (const url of urls) {
    await broadcast(url, bot, token, state, msg.chat.id.toString(), sharedBy);
  }
}

function collectTestFlightUrls(msg: TGMessage): string[] {
  const urls = new Set<string>();
  if (msg.text) extractTestFlightLinks(msg.text).forEach((u) => urls.add(u));
  if (msg.entities) {
    for (const e of msg.entities) {
      if ((e.type === 'text_link' || e.type === 'url') && e.url && isTestFlightUrl(e.url)) {
        urls.add(e.url);
      }
    }
  }
  return Array.from(urls);
}

async function handleCommand(
  msg: TGMessage,
  bot: BotConfig,
  token: string,
  state: State,
  isAdmin: boolean,
): Promise<void> {
  const text = msg.text!;
  const cmd = text.split(/\s+/)[0].toLowerCase().split('@')[0];
  const chatId = msg.chat.id.toString();

  switch (cmd) {
    case '/start':
    case '/help':
      await sendMessage(token, { chat_id: chatId, text: helpText(isAdmin) });
      return;

    case '/id': {
      if (!isAdmin) return;
      const target = argTail(text);
      if (target) {
        await replyLookupId(token, msg, target);
      } else {
        await sendMessage(token, {
          chat_id: chatId,
          text: `your user_id: <code>${msg.from!.id}</code>`,
          parse_mode: 'HTML',
        });
      }
      return;
    }

    case '/groups':
      if (!isAdmin) return;
      await sendMessage(token, {
        chat_id: chatId,
        text: await renderGroups(bot, state),
        parse_mode: 'HTML',
      });
      return;

    case '/addgroup': {
      if (!isAdmin) return;
      const line = argTail(text);
      if (!line) {
        await sendMessage(token, {
          chat_id: chatId,
          text: 'usage: /addgroup name|chat_id|thread_id?',
        });
        return;
      }
      const r = await state.addGroup(line);
      const replyText = r.ok
        ? `added: ${escapeHtml(r.group!.label ?? '')} → <code>${r.group!.chat_id}</code>` +
          (r.group!.thread_id ? ` (thread <code>${r.group!.thread_id}</code>)` : '')
        : `failed: ${escapeHtml(r.reason ?? 'unknown')}`;
      await sendMessage(token, {
        chat_id: chatId,
        text: replyText,
        parse_mode: 'HTML',
      });
      return;
    }

    case '/rmgroup': {
      if (!isAdmin) return;
      const target = argTail(text);
      if (!target) {
        await sendMessage(token, { chat_id: chatId, text: 'usage: /rmgroup <chat_id>' });
        return;
      }
      const removed = await state.removeGroup(target);
      await sendMessage(token, {
        chat_id: chatId,
        text: removed
          ? `removed <code>${escapeHtml(target)}</code>`
          : `not found: <code>${escapeHtml(target)}</code>`,
        parse_mode: 'HTML',
      });
      return;
    }

    case '/quota': {
      if (!isAdmin) return;
      const q = await state.quotaStatus();
      await sendMessage(token, {
        chat_id: chatId,
        text: `quota ${q.count}/${q.limit} used today (${q.date} VN), ${q.remaining} remaining`,
      });
      return;
    }

    case '/setlimit': {
      if (!isAdmin) return;
      const n = Number.parseInt(argTail(text), 10);
      if (!Number.isFinite(n) || n <= 0) {
        await sendMessage(token, { chat_id: chatId, text: 'usage: /setlimit <positive integer>' });
        return;
      }
      await state.setDailyLimit(n);
      await sendMessage(token, { chat_id: chatId, text: `daily limit set to ${n}` });
      return;
    }

    case '/admins': {
      if (!isAdmin) return;
      const list = await state.listAdmins();
      const replyText =
        list.length === 0
          ? 'no admins configured'
          : `admins (${list.length}):\n` +
            list.map((id) => `• <code>${id}</code>`).join('\n');
      await sendMessage(token, { chat_id: chatId, text: replyText, parse_mode: 'HTML' });
      return;
    }

    case '/addadmin': {
      if (!isAdmin) return;
      const id = Number.parseInt(argTail(text), 10);
      if (!Number.isFinite(id) || id <= 0) {
        await sendMessage(token, { chat_id: chatId, text: 'usage: /addadmin <user_id>' });
        return;
      }
      const r = await state.addAdmin(id);
      await sendMessage(token, {
        chat_id: chatId,
        parse_mode: 'HTML',
        text: r.ok
          ? `added admin: <code>${id}</code>`
          : `failed: ${escapeHtml(r.reason ?? 'unknown')}`,
      });
      return;
    }

    case '/rmadmin': {
      if (!isAdmin) return;
      const id = Number.parseInt(argTail(text), 10);
      if (!Number.isFinite(id) || id <= 0) {
        await sendMessage(token, { chat_id: chatId, text: 'usage: /rmadmin <user_id>' });
        return;
      }
      const r = await state.removeAdmin(id);
      await sendMessage(token, {
        chat_id: chatId,
        parse_mode: 'HTML',
        text: r.ok
          ? `removed admin: <code>${id}</code>`
          : `failed: ${escapeHtml(r.reason ?? 'unknown')}`,
      });
      return;
    }

    case '/discord': {
      if (!isAdmin) return;
      const url = await state.getDiscordWebhook();
      await sendMessage(token, {
        chat_id: chatId,
        parse_mode: 'HTML',
        text: url
          ? `Discord webhook:\n<code>${escapeHtml(url)}</code>`
          : 'no Discord webhook set. add one with /setdiscord <url>',
      });
      return;
    }

    case '/setdiscord': {
      if (!isAdmin) return;
      const url = argTail(text);
      if (!url) {
        await sendMessage(token, {
          chat_id: chatId,
          text: 'usage: /setdiscord https://discord.com/api/webhooks/<id>/<token>',
        });
        return;
      }
      const r = await state.setDiscordWebhook(url);
      await sendMessage(token, {
        chat_id: chatId,
        text: r.ok ? 'Discord webhook updated' : `failed: ${r.reason}`,
      });
      return;
    }

    case '/rmdiscord': {
      if (!isAdmin) return;
      const removed = await state.clearDiscordWebhook();
      await sendMessage(token, {
        chat_id: chatId,
        text: removed ? 'Discord webhook removed' : 'no Discord webhook was set',
      });
      return;
    }

  }
}

function helpText(isAdmin: boolean): string {
  if (!isAdmin) return 'Send TestFlight links to broadcast them.';
  return (
    'Send TestFlight links to broadcast them.\n\n' +
    'admin:\n' +
    '/id — print your user_id\n' +
    '/id @username[/thread_id] | chat_id — look up any public chat (prints /addgroup line)\n' +
    '/groups — list configured target groups\n' +
    '/addgroup name|chat_id|thread_id? — add a group\n' +
    '/rmgroup chat_id — remove a group\n' +
    '/admins — list admin user ids\n' +
    '/addadmin <user_id> — grant admin to a user\n' +
    '/rmadmin <user_id> — revoke admin (cannot remove the last admin)\n' +
    '/discord — show current Discord webhook\n' +
    '/setdiscord <url> — set Discord webhook (mirrors broadcasts)\n' +
    '/rmdiscord — remove Discord webhook\n' +
    '/quota — today’s webhook hit count (every message to the bot uses 1)\n' +
    '/setlimit N — change daily limit'
  );
}

async function replyLookupId(
  token: string,
  msg: TGMessage,
  target: string,
): Promise<void> {
  // Accept: @username, username, t.me/username, @username/<thread>, <chat_id>, <chat_id>/<thread>
  let raw = target.trim();
  raw = raw.replace(/^https?:\/\/t\.me\//i, '');
  raw = raw.replace(/^t\.me\//i, '');
  raw = raw.replace(/^@/, '');

  const slashIdx = raw.indexOf('/');
  const handle = slashIdx === -1 ? raw : raw.slice(0, slashIdx);
  const threadStr = slashIdx === -1 ? '' : raw.slice(slashIdx + 1);
  const threadId = /^\d+$/.test(threadStr) ? Number.parseInt(threadStr, 10) : undefined;
  const lookupRef = /^-?\d+$/.test(handle) ? handle : '@' + handle;

  const r = await fetch(
    `https://api.telegram.org/bot${token}/getChat?chat_id=${encodeURIComponent(lookupRef)}`,
  );
  const data = (await r.json().catch(() => null)) as
    | { ok: true; result: { id: number; title?: string; type: string; username?: string } }
    | { ok: false; description?: string }
    | null;

  const chatId = msg.chat.id.toString();
  if (!data || !data.ok) {
    const reason = data && !data.ok ? data.description ?? 'unknown' : 'no response';
    await sendMessage(token, {
      chat_id: chatId,
      text: `getChat failed for ${escapeHtml(lookupRef)}: ${escapeHtml(reason)}`,
    });
    return;
  }

  // Slug: prefer the input @username (preserves case the user typed), fall
  // back to the chat title if the input was numeric.
  const slug = /^-?\d+$/.test(handle)
    ? ((data.result.title ?? data.result.username ?? 'Group').replace(/[|\s]+/g, '') || 'Group')
    : handle;
  const threadPart = threadId !== undefined ? `|${threadId}` : '';
  const line = `/addgroup ${slug}|${data.result.id}${threadPart}`;

  await sendMessage(token, {
    chat_id: chatId,
    text: `<code>${escapeHtml(line)}</code>`,
    parse_mode: 'HTML',
  });
}

function argTail(text: string): string {
  const idx = text.indexOf(' ');
  return idx === -1 ? '' : text.slice(idx + 1).trim();
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]!);
}


async function renderGroups(_bot: BotConfig, state: State): Promise<string> {
  const groups = await state.listGroups();
  const discordWebhook = await state.getDiscordWebhook();
  if (!groups.length && !discordWebhook) {
    return 'no groups configured. add one with /addgroup';
  }
  const lines = groups.map((g) => {
    const label = escapeHtml(g.label ?? '(unlabeled)');
    const thread = g.thread_id ? ` thread <code>${g.thread_id}</code>` : '';
    return `• ${label} — <code>${g.chat_id}</code>${thread}`;
  });
  const discord = discordWebhook ? '\n• Discord webhook configured (use /discord to view)' : '';
  return `targets ${groups.length} group(s):\n${lines.join('\n')}${discord}`;
}

async function broadcast(
  url: string,
  _bot: BotConfig,
  token: string,
  state: State,
  adminChatId: string,
  sharedBy: string,
): Promise<void> {
  let name: string | null = null;
  try {
    name = await fetchAppName(url);
  } catch (e) {
    console.error(`fetchAppName failed for ${url}:`, e);
    return;
  }
  if (!name) return;

  const groups = await state.listGroups();
  if (!groups.length) {
    await sendMessage(token, {
      chat_id: adminChatId,
      text: 'no groups configured. add one with /addgroup',
    });
    return;
  }

  const text = formatBroadcast(name, url, sharedBy);
  const tasks: Promise<unknown>[] = groups.map((g) =>
    sendMessage(token, {
      chat_id: g.chat_id,
      message_thread_id: g.thread_id,
      text,
    }),
  );
  const discordWebhook = await state.getDiscordWebhook();
  if (discordWebhook) tasks.push(sendDiscord(discordWebhook, text));
  await Promise.allSettled(tasks);
}

function formatBroadcast(name: string, url: string, sharedBy: string): string {
  return (
    `${nameToHashtag(name)}\n\n` +
    `Join the ${name} beta on ✈️ #TestFlight\n\n` +
    `🔗 Link: ${url}\n\n` +
    `Shared by ${sharedBy}`
  );
}

