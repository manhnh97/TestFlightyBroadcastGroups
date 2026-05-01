import { DurableObject } from 'cloudflare:workers';
import type { Group } from './config';
import { DEFAULT_DAILY_LIMIT } from './config';
import { todayVN } from './time';

const GROUPS_KEY = 'groups';
const ADMINS_KEY = 'admins';
const LIMIT_KEY = 'limit';
const QUOTA_KEY = 'quota';

type StoredQuota = { date: string; count: number };

export type QuotaStatus = {
  date: string;
  count: number;
  limit: number;
  remaining: number;
};

export type ConsumeResult = QuotaStatus & { ok: boolean };

// One DO instance per bot (named by bot_id). Holds the current group list and
// today's broadcast counter. All mutations go through Telegram admin commands.
export class BotStateDO extends DurableObject {
  // ---- groups ----------------------------------------------------------

  async ensureSeeded(seed: string[]): Promise<void> {
    if (!seed?.length) return;
    const existing = await this.ctx.storage.get<string[]>(GROUPS_KEY);
    if (existing !== undefined) return;
    const cleaned = seed.filter((line) => tryParseGroupLine(line) !== null);
    await this.ctx.storage.put(GROUPS_KEY, cleaned);
  }

  async listGroupLines(): Promise<string[]> {
    return (await this.ctx.storage.get<string[]>(GROUPS_KEY)) ?? [];
  }

  async listGroups(): Promise<Group[]> {
    const lines = await this.listGroupLines();
    return lines
      .map(tryParseGroupLine)
      .filter((g): g is Group => g !== null);
  }

  async addGroup(line: string): Promise<{ ok: boolean; reason?: string; group?: Group }> {
    const parsed = tryParseGroupLine(line);
    if (!parsed) {
      return { ok: false, reason: 'invalid format. expected: name|chat_id|thread_id?' };
    }
    const lines = await this.listGroupLines();
    const filtered = lines.filter(
      (l) => tryParseGroupLine(l)?.chat_id !== parsed.chat_id,
    );
    filtered.push(formatGroup(parsed));
    await this.ctx.storage.put(GROUPS_KEY, filtered);
    return { ok: true, group: parsed };
  }

  async removeGroup(chatId: string): Promise<boolean> {
    const lines = await this.listGroupLines();
    const filtered = lines.filter((l) => tryParseGroupLine(l)?.chat_id !== chatId);
    if (filtered.length === lines.length) return false;
    await this.ctx.storage.put(GROUPS_KEY, filtered);
    return true;
  }

  // ---- admins ----------------------------------------------------------

  async ensureSeededAdmins(seed: number[]): Promise<void> {
    if (!seed?.length) return;
    const existing = await this.ctx.storage.get<number[]>(ADMINS_KEY);
    if (existing !== undefined) return;
    await this.ctx.storage.put(ADMINS_KEY, [...new Set(seed)]);
  }

  async listAdmins(): Promise<number[]> {
    return (await this.ctx.storage.get<number[]>(ADMINS_KEY)) ?? [];
  }

  async addAdmin(userId: number): Promise<{ ok: boolean; reason?: string }> {
    if (!Number.isFinite(userId) || userId <= 0) {
      return { ok: false, reason: 'invalid user id' };
    }
    const list = await this.listAdmins();
    if (list.includes(userId)) return { ok: false, reason: 'already an admin' };
    list.push(userId);
    await this.ctx.storage.put(ADMINS_KEY, list);
    return { ok: true };
  }

  async removeAdmin(userId: number): Promise<{ ok: boolean; reason?: string }> {
    const list = await this.listAdmins();
    if (!list.includes(userId)) return { ok: false, reason: 'not an admin' };
    if (list.length <= 1) return { ok: false, reason: 'cannot remove the last admin' };
    await this.ctx.storage.put(ADMINS_KEY, list.filter((id) => id !== userId));
    return { ok: true };
  }

  // ---- daily quota -----------------------------------------------------

  async setDailyLimit(limit: number): Promise<void> {
    await this.ctx.storage.put(LIMIT_KEY, limit);
  }

  async ensureDailyLimit(seedLimit: number | undefined): Promise<void> {
    if (seedLimit === undefined) return;
    const existing = await this.ctx.storage.get<number>(LIMIT_KEY);
    if (existing !== undefined) return;
    await this.ctx.storage.put(LIMIT_KEY, seedLimit);
  }

  async getDailyLimit(): Promise<number> {
    return (await this.ctx.storage.get<number>(LIMIT_KEY)) ?? DEFAULT_DAILY_LIMIT;
  }

  async quotaStatus(): Promise<QuotaStatus> {
    const limit = await this.getDailyLimit();
    const today = todayVN();
    const cur = await this.ctx.storage.get<StoredQuota>(QUOTA_KEY);
    const count = cur && cur.date === today ? cur.count : 0;
    return { date: today, count, limit, remaining: Math.max(0, limit - count) };
  }

  // Atomic consume: rolls the day if needed, refuses past the limit.
  async tryConsume(): Promise<ConsumeResult> {
    const limit = await this.getDailyLimit();
    const today = todayVN();
    let cur = await this.ctx.storage.get<StoredQuota>(QUOTA_KEY);
    if (!cur || cur.date !== today) cur = { date: today, count: 0 };
    if (cur.count >= limit) {
      return { ok: false, date: today, count: cur.count, limit, remaining: 0 };
    }
    cur.count += 1;
    await this.ctx.storage.put(QUOTA_KEY, cur);
    return { ok: true, date: today, count: cur.count, limit, remaining: limit - cur.count };
  }
}

// ---- helpers ----------------------------------------------------------

export function tryParseGroupLine(line: string): Group | null {
  const parts = line.split('|').map((s) => s.trim());
  if (parts.length < 2 || parts.length > 3) return null;
  const [name, chatId, threadStr] = parts;
  if (!name || !chatId) return null;
  const group: Group = { chat_id: chatId, label: name };
  if (threadStr) {
    const tid = Number.parseInt(threadStr, 10);
    if (!Number.isFinite(tid)) return null;
    group.thread_id = tid;
  }
  return group;
}

export function formatGroup(g: Group): string {
  const parts: string[] = [g.label ?? '', g.chat_id];
  if (g.thread_id !== undefined) parts.push(String(g.thread_id));
  return parts.join('|');
}
