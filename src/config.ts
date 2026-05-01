// Single-bot config. Token comes from the BOT_TOKENS secret (plain string,
// not JSON). All other config lives here.

export type Group = {
  chat_id: string;       // -100... for supergroups/channels
  thread_id?: number;    // forum/topic id (omit for non-forum groups)
  label?: string;        // shown in /groups output
};

export type Contact = {
  chat_id: string;
  thread_id?: number;
};

export type BotConfig = {
  // Initial Telegram user ids allowed to broadcast & manage the bot. Written
  // to the DO ONLY if the DO has no admin list yet. After first run, manage
  // admins via /addadmin and /rmadmin — edits to this array are ignored.
  // To find your id, message @userinfobot on Telegram.
  seedAdmins: number[];

  // Initial /cc forwarding target (also used for error reports). Written to
  // the DO ONLY if the DO has no contact yet. After first run, manage via
  // /setcontact and /rmcontact — edits to this field are ignored.
  seedContact?: Contact;

  // Initial Discord webhook to mirror broadcasts. Written to the DO ONLY if
  // the DO has no webhook yet. After first run, manage via /setdiscord and
  // /rmdiscord — edits to this field are ignored.
  seedDiscordWebhook?: string;

  // Broadcasts/day. Default 200. Mutable at runtime via /setlimit.
  dailyLimit?: number;

  // Override for the "Shared by ..." footer line. If omitted, the admin's
  // Telegram first_name is used.
  sharedBy?: string;

  // Initial groups, written to the DO ONLY if the DO has no groups yet.
  // Format: "name|chat_id|thread_id" (thread_id optional). Edits to this
  // array after the first deploy are ignored — use /addgroup or /rmgroup.
  seedGroups?: string[];
};

export const DEFAULT_DAILY_LIMIT = 200;

export const BOT: BotConfig = {
  seedAdmins: [863875519, 6325914189],
  seedContact: { chat_id: '-1002031575789', thread_id: 11 },
  seedDiscordWebhook:
    'https://discord.com/api/webhooks/1210607511024177202/MqV1JFSHYhawyL6TIbaAMiiDRlQCueE4Xt-NkRBD0cSaGDNePaS1aEb8LjhMIukwg2xx',
  dailyLimit: 200,
  seedGroups: [
    'Nghien|-1001236644871|235212',
    'Testflight1110|-1002112742740',
    'HahiOS|-1001590452930|1742',
    'TestFlightM|-1002097016460',
    'KGM|-1001823403288|32',
  ],
};
