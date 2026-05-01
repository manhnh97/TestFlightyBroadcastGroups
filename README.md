# Testflight_SendGroups

Cloudflare Worker that broadcasts TestFlight links from a Telegram private chat to multiple groups/topics. Group lists and per-bot daily quotas are stored in a Durable Object — change them at runtime via Telegram commands, no redeploy.

## Architecture

- One Worker handles all bots, routed by webhook path: `/webhook/<bot_id>`.
- One Durable Object instance per bot (named by `bot_id`) holds:
  - Groups, stored as `name|chat_id|thread_id?` lines.
  - Daily broadcast counter (resets at 00:00 Asia/Ho_Chi_Minh, UTC+7).
  - Daily limit (default 200, mutable via `/setlimit`).
- Static config ([`src/config.ts`](src/config.ts)) holds admins, contact target, Discord webhook, and **seed** values (groups + limit) used only on first run.
- Only one env secret: `BOT_TOKENS`, a JSON map of `bot_id → token`.

## Setup

```bash
npm install
wrangler login
wrangler secret put BOT_TOKENS
# paste a single line of JSON, e.g.:
# {"remindslow":"6717549493:AAE...","testflightx":"6997135775:AAF...","campingapps":"6675183376:AAF..."}

npm run deploy
```

Worker URL will look like `https://testflight-bots.<your-subdomain>.workers.dev`.

## Register the webhook for each bot

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<URL>/webhook/remindslow"
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<URL>/webhook/testflightx"
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<URL>/webhook/campingapps"
```

Verify with `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`.

## Bot commands

| Command | Who | What |
|---|---|---|
| `/start`, `/help` | anyone | usage hint |
| `/cc <message>` | anyone | forwards a message to the contact group |
| `/id` | admins | reply with `chat_id` / `thread_id` of the current chat (works in any chat) |
| `/groups` | admins | list current target groups (from DO) |
| `/addgroup name\|chat_id\|thread_id?` | admins | add or update a group |
| `/rmgroup chat_id` | admins | remove a group |
| `/quota` | admins | today's broadcast count (`used / limit`) |
| `/setlimit N` | admins | change the daily broadcast limit |
| _(any TestFlight link)_ | admins, private chat | fetch app name, broadcast (consumes 1 quota) |

Admins are listed in `BotConfig.admins` in [`src/config.ts`](src/config.ts).

## Updating groups (the dynamic part)

Send the bot a private-chat command. No redeploy:

```
/addgroup MyNewGroup|-1001234567890|42
/rmgroup -1001234567890
/groups
```

`thread_id` is optional — omit it for non-forum groups:
```
/addgroup PlainGroup|-1001234567890
```

## Seeding

`seedGroups` and `dailyLimit` in `src/config.ts` are written to the DO **only on first use** (when the DO has no value yet). After that, runtime commands win. To re-seed, delete the DO instance with `wrangler` or change values directly via commands.

## Local dev

```bash
npm run dev      # local worker on :8787
npm run tail     # stream production logs
npm run typecheck
```

## Files

```
src/
  index.ts            # HTTP entry, /webhook/<bot_id> router
  config.ts           # bots: admins, contact, discord, seedGroups, dailyLimit
  handlers.ts         # update dispatch, /cc, /groups, /addgroup, /rmgroup, /quota, /setlimit, broadcast
  telegram.ts         # sendMessage / Discord helpers
  testflight.ts       # link regex, title fetch, hashtag builder
  durable-objects.ts  # BotStateDO: group storage + DailyQuotaLimiter
wrangler.toml         # DO binding + migration
```
