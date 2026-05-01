// Static config: tokens (BOT_TOKENS secret), admins, contact target, Discord webhook,
// daily quota, and one-time group seeds. Group changes after first deploy happen via
// Telegram commands (/addgroup, /rmgroup) and persist in a Durable Object.

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
  id: string;            // matches /webhook/<id> path and BOT_TOKENS key
  admins: number[];      // user ids allowed to broadcast & manage groups
  contact?: Contact;     // /cc forwarding target (also used for error reports)
  discordWebhook?: string;
  dailyLimit?: number;   // broadcasts/day (default 200)

  // Override for the "Shared by ..." footer line in broadcasts. If omitted,
  // the admin's Telegram first_name is used.
  sharedBy?: string;

  // Initial groups, written to the DO ONLY if the DO has no groups yet.
  // Format: "name|chat_id|thread_id" (thread_id optional). Edits to this
  // array after the first deploy are ignored — use /addgroup or /rmgroup.
  seedGroups?: string[];
};

export const DEFAULT_DAILY_LIMIT = 200;

export const BOTS: Record<string, BotConfig> = {
  remindslow: {
    id: 'remindslow',
    admins: [863875519, 6325914189],
    contact: { chat_id: '-1002031575789', thread_id: 11 },
    discordWebhook:
      'https://discord.com/api/webhooks/1210607511024177202/MqV1JFSHYhawyL6TIbaAMiiDRlQCueE4Xt-NkRBD0cSaGDNePaS1aEb8LjhMIukwg2xx',
    dailyLimit: 200,
    seedGroups: [
      'Nghien|-1001236644871|235212',
      'Testflight1110|-1002112742740',
      'HahiOS|-1001590452930|1742',
      'TestFlightM|-1002097016460',
      'KGM|-1001823403288|32',
    ],
  },

  testflightx: {
    id: 'testflightx',
    admins: [863875519, 6325914189],
    contact: { chat_id: '-1002031575789', thread_id: 11 },
    dailyLimit: 200,
    seedGroups: [
      'TestFlightX channel|-1001363951322',
      'TestFlight Reviews|-1001170452834',
    ],
  },

  campingapps: {
    id: 'campingapps',
    admins: [863875519, 6325914189],
    contact: { chat_id: '-1002031575789', thread_id: 11 },
    dailyLimit: 200,
    seedGroups: [
      'CampingApps Dashboard|-1002117624357',
    ],
  },
};
