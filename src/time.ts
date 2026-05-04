// Vietnam time helpers. Asia/Ho_Chi_Minh = UTC+7, no DST.

const VN_OFFSET_MS = 7 * 60 * 60 * 1000;

// "YYYY-MM-DD" in VN time. Used as the quota day key.
export function todayVN(): string {
  return new Date(Date.now() + VN_OFFSET_MS).toISOString().slice(0, 10);
}
