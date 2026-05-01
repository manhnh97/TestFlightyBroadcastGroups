// Vietnam time helpers. Asia/Ho_Chi_Minh = UTC+7, no DST.
// Used everywhere this project formats a date or timestamp.

const VN_OFFSET_MS = 7 * 60 * 60 * 1000;

function shifted(): Date {
  return new Date(Date.now() + VN_OFFSET_MS);
}

// "YYYY-MM-DD" in VN time. Used as the quota day key.
export function todayVN(): string {
  return shifted().toISOString().slice(0, 10);
}

// "YYYY-MM-DD HH:MM:SS" in VN time. Used in error reports and contact forwards.
export function nowVN(): string {
  return shifted().toISOString().slice(0, 19).replace('T', ' ');
}
