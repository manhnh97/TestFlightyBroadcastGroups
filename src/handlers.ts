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
  const isAdmin = bot.admins.includes(msg.from.id);

  if (!isPrivate) return;

  if (text.startsWith('/')) {
    await handleCommand(msg, bot, token, state);
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
): Promise<void> {
  const text = msg.text!;
  const cmd = text.split(/\s+/)[0].toLowerCase().split('@')[0];
  const chatId = msg.chat.id.toString();
  const user = msg.from!;
  const isAdmin = bot.admins.includes(user.id);

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
        parse_mode: 'Markdown',
      });
      return;

    case '/addgroup': {
      if (!isAdmin) return;
      const line = argTail(text);
      if (!line) {
        await sendMessage(token, {
          chat_id: chatId,
          text: 'usage: `/addgroup name|chat_id|thread_id?`',
          parse_mode: 'Markdown',
        });
        return;
      }
      const r = await state.addGroup(line);
      await sendMessage(token, {
        chat_id: chatId,
        text: r.ok
          ? `added: ${r.group!.label} → \`${r.group!.chat_id}\`${
              r.group!.thread_id ? ` (thread \`${r.group!.thread_id}\`)` : ''
            }`
          : `failed: ${r.reason}`,
        parse_mode: 'Markdown',
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
        text: removed ? `removed \`${target}\`` : `not found: \`${target}\``,
        parse_mode: 'Markdown',
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
    '/quota — today’s broadcast count\n' +
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
      text: `your chat_id: \`${chatId}\`\n\nusage: \`/id @username\` to look up a public group / channel`,
      parse_mode: 'Markdown',
    });
    return;
  }

  const ref = arg.startsWith('@') ? arg : '@' + arg;
  const chat = await getChat(token, ref);
  if (!chat) {
    await sendMessage(token, {
      chat_id: chatId,
      text: `not found, or the bot can't access \`${ref}\`. it must be public, or the bot must be a member.`,
      parse_mode: 'Markdown',
    });
    return;
  }

  const title = chat.title ?? chat.username ?? '(unknown)';
  const suggestedName = (chat.title ?? chat.username ?? 'Group').replace(/\|/g, '_');
  const addLine = `/addgroup ${suggestedName}|${chat.id}`;

  await sendMessage(token, {
    chat_id: chatId,
    text: [
      `chat: ${title} (${chat.type})`,
      `chat_id: \`${chat.id}\``,
      '',
      `\`${addLine}\``,
      '',
      '_Note: thread_id (for forum topics) cannot be looked up by username — append it manually if needed._',
    ].join('\n'),
    parse_mode: 'Markdown',
  });
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

async function renderGroups(bot: BotConfig, state: State): Promise<string> {
  const groups = await state.listGroups();
  if (!groups.length) return 'no groups configured. add one with /addgroup';
  const lines = groups.map((g) => {
    const thread = g.thread_id ? ` thread \`${g.thread_id}\`` : '';
    return `• ${g.label ?? '(unlabeled)'} — \`${g.chat_id}\`${thread}`;
  });
  const discord = bot.discordWebhook ? '\n• Discord webhook configured' : '';
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

  const consume = await state.tryConsume();
  if (!consume.ok) {
    await sendMessage(token, {
      chat_id: adminChatId,
      text: `quota exceeded (${consume.count}/${consume.limit}). resets at 00:00 VN time.`,
    });
    return;
  }

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
      disable_web_page_preview: true,
    }),
  );
  if (bot.discordWebhook) tasks.push(sendDiscord(bot.discordWebhook, text));
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
