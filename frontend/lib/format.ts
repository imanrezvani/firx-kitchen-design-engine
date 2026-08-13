const FA_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

export function toFa(input: string | number): string {
  return String(input).replace(/[0-9]/g, (d) => FA_DIGITS[Number(d)]);
}

export function faNumber(n: number | null | undefined): string {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return toFa(Math.round(n).toLocaleString("en-US"));
}

/** Convert a Gregorian date to a Jalali (Persian) calendar date string. */
export function toJalali(iso: string | Date): string {
  const d = typeof iso === "string" ? new Date(iso) : iso;
  if (isNaN(d.getTime())) return toFa(new Date().getFullYear());
  const j = gregorianToJalali(d);
  return `${toFa(j[0])}/${toFa(j[1].toString().padStart(2, "0"))}/${toFa(j[2].toString().padStart(2, "0"))}`;
}

/** gregorianToJalali returns [jy, jm, jd]. */
export function gregorianToJalali(d: Date): [number, number, number] {
  const gy = d.getFullYear();
  const gm = d.getMonth() + 1;
  const gd = d.getDate();
  const gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  const gy2 = gm > 2 ? gy + 1 : gy;
  const days =
    355666 + 365 * gy + Math.floor((gy2 + 3) / 4) - Math.floor((gy2 + 99) / 100) + Math.floor((gy2 + 399) / 400) + gd + gdm[gm - 1];
  let jy = -1595 + 33 * Math.floor(days / 12053);
  let day = days % 12053;
  jy += 4 * Math.floor(day / 1461);
  day %= 1461;
  if (day > 365) {
    jy += Math.floor((day - 1) / 365);
    day = (day - 1) % 365;
  }
  let jm: number, jd: number;
  if (day < 186) {
    jm = 1 + Math.floor(day / 31);
    jd = 1 + (day % 31);
  } else {
    jm = 7 + Math.floor((day - 186) / 30);
    jd = 1 + ((day - 186) % 30);
  }
  return [jy, jm, jd];
}

export const LAYOUT_FA: Record<string, string> = {
  linear: "خطی",
  L: "L شکل",
  U: "U شکل",
  galley: "دوطرفه / گالی",
  island: "جزیره",
  peninsula: "شبه‌جزیره",
};

export const STATUS_FA: Record<string, { label: string; color: string }> = {
  draft: { label: "پیش‌نویس", color: "gray" },
  designing: { label: "در حال طراحی", color: "blue" },
  needs_review: { label: "نیازمند بررسی", color: "amber" },
  approved: { label: "تأیید شده", color: "green" },
  completed: { label: "تکمیل‌شده", color: "green" },
  archived: { label: "بایگانی‌شده", color: "gray" },
};
