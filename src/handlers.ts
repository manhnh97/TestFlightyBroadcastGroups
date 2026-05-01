import type { BotConfig } from './config';
import type { BotStateDO } from './durable-objects';
import { sendMessage, sendDiscord, getChat } from './telegram';
import {
  extractTestFlightLinks,
  fetchAppName,
  isTestFlightUrl,
  nameToHashtag,
} from './testflight';
import { nowVN } from './time';

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

    case '/cc':
      await handleContact(msg, bot, token, argTail(text));
      return;

    case '/id':
      if (!isAdmin) return;
      await handleId(token, chatId, argTail(text));
      return;

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
  const base =
    'Send TestFlight links to broadcast them.\n\n' +
    '/cc <message> — contact the admin\n';
  if (!isAdmin) return base;
  return (
    base +
    '\nadmin:\n' +
    '/id [@username] — your own chat_id, or look up a public group/channel by username\n' +
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

function argTail(text: string): string {
  const idx = text.indexOf(' ');
  return idx === -1 ? '' : text.slice(idx + 1).trim();
}

async function handleId(token: string, chatId: string, arg: string): Promise<void> {
  // No arg: report the caller's own chat_id (their Telegram user id, since
  // this is a private chat).
  if (!arg) {
    await sendMessage(token, {
      chat_id: chatId,
      text: `your chat_id: ${chatId}\n\nusage: /id @username — look up a public supergroup or channel`,
    });
    return;
  }

  const ref = arg.startsWith('@') ? arg : '@' + arg;

  let chat;
  try {
    chat = await getChat(token, ref);
  } catch (e) {
    await sendMessage(token, {
      chat_id: chatId,
      text: `lookup error for ${ref}: ${(e as Error).message}`,
    });
    return;
  }

  if (!chat) {
    await sendMessage(token, {
      chat_id: chatId,
      text:
        `not found: ${ref}\n\n` +
        `getChat only resolves public supergroups and channels. Users, bots, ` +
        `and private chats can't be looked up by @username.`,
    });
    return;
  }

  const title = chat.title ?? chat.username ?? '(unknown)';
  // Collapse any run of whitespace and/or pipes into a single underscore so
  // the suggested name is a valid single token in the pipe-delimited format
  // ("TestFlighty | Notification" -> "TestFlighty_Notification").
  const suggestedName = (chat.title ?? chat.username ?? 'Group')
    .replace(/[\s|]+/g, '_')
    .replace(/^_+|_+$/g, '');
  const addLine = `/addgroup ${suggestedName}|${chat.id}`;

  await sendMessage(token, {
    chat_id: chatId,
    parse_mode: 'HTML',
    text: [
      `chat: ${escapeHtml(title)} (${chat.type})`,
      `chat_id: <code>${chat.id}</code>`,
      '',
      `<code>${escapeHtml(addLine)}</code>`,
      '',
      'thread_id (forum topics) cannot be looked up by username — append it manually if needed.',
    ].join('\n'),
  });
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]!);
}

async function handleContact(
  msg: TGMessage,
  bot: BotConfig,
  token: string,
  body: string,
): Promise<void> {
  const user = msg.from!;
  const chatId = msg.chat.id.toString();

  await sendMessage(token, {
    chat_id: chatId,
    text: `Thanks ${user.first_name ?? ''}, your message is important to me and I will respond as soon as possible.`,
  });

  if (!bot.contact || !body) return;

  await sendMessage(token, {
    chat_id: bot.contact.chat_id,
    message_thread_id: bot.contact.thread_id,
    text:
      `[${nowVN()} VN] /cc\n` +
      `chat_id: ${user.id}\nusername: ${user.username ?? '(none)'}\nmessage: ${body}`,
  });
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
  bot: BotConfig,
  token: string,
  state: State,
  adminChatId: string,
  sharedBy: string,
): Promise<void> {
  let name: string | null = null;
  try {
    name = await fetchAppName(url);
  } catch (e) {
    await reportError(bot, token, `fetchAppName failed for ${url}: ${(e as Error).message}`);
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

async function reportError(bot: BotConfig, token: string, message: string): Promise<void> {
  if (!bot.contact) return;
  await sendMessage(token, {
    chat_id: bot.contact.chat_id,
    message_thread_id: bot.contact.thread_id,
    text: `[${nowVN()} VN] ${message}`,
  }).catch(() => {});
}
