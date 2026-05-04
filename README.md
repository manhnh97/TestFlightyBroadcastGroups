# Testflight_SendGroups

Cloudflare Worker that broadcasts TestFlight links from a Telegram private chat to multiple groups/topics. One bot, one Worker. The group list, admin list, Discord mirror, and daily quota live in a Durable Object — change them from Telegram, no redeploy.

## Architecture

- Single Worker. Single bot. Webhook path: `/webhook`.
- One Durable Object instance (`BotStateDO`) holds:
  - Groups, stored as `name|chat_id|thread_id?` lines.
  - Admin Telegram user IDs.
  - Discord webhook URL (optional, mirrors broadcasts).
  - Daily broadcast counter (resets at 00:00 Asia/Ho_Chi_Minh, UTC+7).
  - Daily limit (default 200, mutable via `/setlimit`).
- Static config ([`src/config.ts`](src/config.ts)) holds **seed** values used only on first run. Runtime commands win after that.
- Only one secret: `BOT_TOKENS`, the bot token as a plain string.

## Prerequisites

- Node.js 18+
- A Cloudflare account (Workers paid plan **not** required — the free tier is enough; Durable Objects with SQLite are free-tier eligible).
- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- Your Telegram user ID (message [@userinfobot](https://t.me/userinfobot) to get it).

## Setup

```bash
git clone <this-repo>
cd Testflight_SendGroups
npm install
```

### 1. Configure seed values

Edit [`src/config.ts`](src/config.ts) before your first deploy:

```ts
export const BOT: BotConfig = {
  seedAdmins: [123456789],          // your Telegram user id(s)
  seedDiscordWebhook: undefined,    // optional, set later via /setdiscord
  dailyLimit: 200,
  seedGroups: [
    // 'GroupName|-1001234567890|42',  // forum topic
    // 'PlainGroup|-1001234567890',    // non-forum
  ],
};
```

These values are written to the Durable Object **only on first run**. After that, manage everything via Telegram commands (`/addadmin`, `/addgroup`, etc.) — edits to `config.ts` after the first deploy are ignored.

### 2. Set the bot token

Use either the dashboard or the CLI:

```bash
wrangler login
wrangler secret put BOT_TOKENS
# paste the token from BotFather (plain string, no quotes, no JSON)
```

Or in the Cloudflare dashboard → Workers & Pages → your worker → **Variables and Secrets** → **Add**:

| Type | Name | Value |
|---|---|---|
| Secret | `BOT_TOKENS` | `1234567890:AAE...` (your bot token) |

### 3. Deploy

```bash
npm run deploy
```

### 4. Register the webhook

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-worker>.workers.dev/webhook"
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

The second call should show your worker URL in `"url"` and an empty `"last_error_message"`.

## Bot commands

| Command | Who | What |
|---|---|---|
| `/start`, `/help` | anyone | usage hint |
| `/groups` | admins | list current target groups (from DO) |
| `/addgroup name\|chat_id\|thread_id?` | admins | add or update a group |
| `/rmgroup chat_id` | admins | remove a group |
| `/admins` | admins | list current admin user ids |
| `/addadmin <user_id>` | admins | grant admin to a user |
| `/rmadmin <user_id>` | admins | revoke admin (the last admin cannot be removed) |
| `/discord` | admins | show current Discord webhook URL |
| `/setdiscord <url>` | admins | set Discord webhook URL (mirrors broadcasts) |
| `/rmdiscord` | admins | remove Discord webhook |
| `/quota` | admins | today's webhook hit count (`used / limit`) |
| `/setlimit N` | admins | change the daily broadcast limit |
| _(any TestFlight link)_ | admins, private chat | fetch app name, broadcast (consumes 1 quota) |

## Updating groups

Send the bot a private-chat command. No redeploy:

```
/addgroup MyGroup|-1001234567890|42
/rmgroup -1001234567890
/groups
```

`thread_id` is optional — omit for non-forum groups:

```
/addgroup PlainGroup|-1001234567890
```

## Local dev

```bash
npm run dev        # local worker on :8787
npm run tail       # stream production logs
npm run typecheck
```

For local dev with secrets, create a `.dev.vars` file (gitignored):

```
BOT_TOKENS=1234567890:AAE...
```

## Files

```
src/
  index.ts            # HTTP entry, /webhook router
  config.ts           # BOT: seedAdmins, seedDiscordWebhook, seedGroups, dailyLimit
  handlers.ts         # commands + broadcast logic
  telegram.ts         # sendMessage / Discord helpers
  testflight.ts       # link regex, title fetch, hashtag, ?nocache
  durable-objects.ts  # BotStateDO: groups, admins, discord, quota
  time.ts             # Vietnam-time helpers
wrangler.toml         # DO binding + migration
```

## Notes

- The daily quota counts **every webhook hit**, not just broadcasts — a chatty group flooding the bot will burn through it. Use `/setlimit` to raise it.
- Quota resets at 00:00 Asia/Ho_Chi_Minh (UTC+7). Adjust [`src/time.ts`](src/time.ts) if you want a different timezone.
- TestFlight title fetches use a `?nocache=<nonce>` cache-buster so each broadcast reads the live status.

## License

[MIT](LICENSE)
