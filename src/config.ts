// Single-bot config. Token comes from the BOT_TOKENS secret (plain string,
// not JSON). All other config lives here.

export type Group = {
  chat_id: string;       // -100... for supergroups/channels
  thread_id?: number;    // forum/topic id (omit for non-forum groups)
  label?: string;        // shown in /groups output
};

export type BotConfig = {
  // Initial Telegram user ids allowed to broadcast & manage the bot. Written
  // to the DO ONLY if the DO has no admin list yet. After first run, manage
  // admins via /addadmin and /rmadmin — edits to this array are ignored.
  // To find your id, message @userinfobot on Telegram.
  seedAdmins: number[];

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
  // Replace with your Telegram user id(s). Message @userinfobot to find yours.
  seedAdmins: [],

  // Optional — leave undefined to skip Discord mirroring, or set later via
  // /setdiscord at runtime.
  seedDiscordWebhook: undefined,

  dailyLimit: 200,

  // Optional initial groups. Format: "name|chat_id|thread_id?".
  // Examples:
  //   'MyForumGroup|-1001234567890|42',
  //   'MyPlainGroup|-1009876543210',
  seedGroups: [],
};
