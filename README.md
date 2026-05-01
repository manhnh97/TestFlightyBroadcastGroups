# Testflight_SendGroups

Cloudflare Worker that broadcasts TestFlight links from a Telegram private chat to multiple groups/topics. One bot. Group list and daily quota live in a Durable Object — change them from Telegram, no redeploy.

## Architecture

- Single Worker. Single bot. Webhook path: `/webhook`.
- One Durable Object instance holds:
  - Groups, stored as `name|chat_id|thread_id?` lines.
  - Daily broadcast counter (resets at 00:00 Asia/Ho_Chi_Minh, UTC+7).
  - Daily limit (default 200, mutable via `/setlimit`).
- Static config ([`src/config.ts`](src/config.ts)) holds admins, contact target, Discord webhook, and **seed** values used only on first run.
- Only one secret: `BOT_TOKENS`, the bot token as a plain string.

## Setup

```bash
npm install
wrangler login
npm run deploy
```

In the Cloudflare dashboard → Workers & Pages → your worker → **Variables and Secrets** → **Add**:

| Type | Name | Value |
|---|---|---|
| Secret | `BOT_TOKENS` | `1234567890:AAE...` (your bot token, no JSON, no quotes) |

Save. The worker picks it up immediately on the next request.

## Register the webhook

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-worker>.workers.dev/webhook"
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

The second call should show your worker URL in `"url"` and an empty `"last_error_message"`.

## Bot commands

| Command | Who | What |
|---|---|---|
| `/start`, `/help` | anyone | usage hint |
| `/cc <message>` | anyone | forwards a message to the contact group |
| `/id [@username]` | admins, private chat | no arg → your own `chat_id`; with `@username` → look up a public group/channel via Telegram's `getChat` |
| `/groups` | admins | list current target groups (from DO) |
| `/addgroup name\|chat_id\|thread_id?` | admins | add or update a group |
| `/rmgroup chat_id` | admins | remove a group |
| `/admins` | admins | list current admin user ids |
| `/addadmin <user_id>` | admins | grant admin to a user |
| `/rmadmin <user_id>` | admins | revoke admin (the last admin cannot be removed) |
| `/discord` | admins | show current Discord webhook URL |
| `/setdiscord <url>` | admins | set Discord webhook URL (mirrors broadcasts) |
| `/rmdiscord` | admins | remove Discord webhook |
| `/contact` | admins | show current `/cc` forwarding target |
| `/setcontact <chat_id> [thread_id]` | admins | set the `/cc` forwarding target |
| `/rmcontact` | admins | remove the `/cc` forwarding target |
| `/quota` | admins | today's webhook hit count (`used / limit`) |
| `/setlimit N` | admins | change the daily broadcast limit |
| _(any TestFlight link)_ | admins, private chat | fetch app name, broadcast (consumes 1 quota) |

Initial admin Telegram user IDs come from `BOT.seedAdmins` in [`src/config.ts`](src/config.ts) — seeded into the Durable Object on first run. After that, manage admins via `/addadmin` and `/rmadmin`. Find your id by messaging `@userinfobot`.

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

## Seeding

`seedGroups`, `seedAdmins`, `seedDiscordWebhook`, `seedContact`, and `dailyLimit` in `src/config.ts` are written to the DO **only on first use** (when the DO has no value yet). After that, runtime commands win. To re-seed, delete the DO instance with `wrangler` or change values directly via commands.

## Local dev

```bash
npm run dev      # local worker on :8787
npm run tail     # stream production logs
npm run typecheck
```

## Files

```
src/
  index.ts            # HTTP entry, /webhook router
  config.ts           # BOT: seedAdmins, seedContact, seedDiscordWebhook, seedGroups, dailyLimit
  handlers.ts         # commands: /cc, /id, /groups, /addgroup, /rmgroup, /admins, /addadmin, /rmadmin, /discord, /setdiscord, /rmdiscord, /quota, /setlimit + broadcast
  telegram.ts         # sendMessage / Discord helpers
  testflight.ts       # link regex, title fetch, hashtag, ?nocache
  durable-objects.ts  # BotStateDO: group storage + DailyQuotaLimiter
  time.ts             # Vietnam-time helpers
wrangler.toml         # DO binding + migration
```
