import { articlesToBuckets } from "../lib/sparkline-buckets";

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

function art(t: number) {
  return { published_at: new Date(t).toISOString() };
}

describe("articlesToBuckets", () => {
  test("returns [] for empty input", () => {
    expect(articlesToBuckets([])).toEqual([]);
  });

  test("returns [] when fewer than 3 articles", () => {
    const now = Date.now();
    expect(articlesToBuckets([art(now - HOUR), art(now - 2 * HOUR)])).toEqual([]);
  });

  test("returns 12 evenly-distributed buckets when articles span full window", () => {
    const now = 24 * DAY;
    const items = Array.from({ length: 12 }, (_, i) => art(now - (i + 0.5) * 2 * HOUR));
    const out = articlesToBuckets(items, 12, DAY, now);
    expect(out).toHaveLength(12);
    for (const v of out) expect(v).toBe(1);
  });

  test("ignores articles in the future (clock skew defense)", () => {
    const now = 24 * DAY;
    const items = [
      art(now - HOUR),
      art(now - 2 * HOUR),
      art(now - 3 * HOUR),
      art(now + HOUR),
    ];
    const out = articlesToBuckets(items, 12, DAY, now);
    expect(out.reduce((a, b) => a + b, 0)).toBe(3);
  });

  test("ignores articles older than the window", () => {
    const now = 24 * DAY;
    const items = [
      art(now - HOUR),
      art(now - 2 * HOUR),
      art(now - 3 * HOUR),
      art(now - 30 * HOUR),
    ];
    const out = articlesToBuckets(items, 12, DAY, now);
    expect(out.reduce((a, b) => a + b, 0)).toBe(3);
  });

  test("uses the bucket boundary [start, end) — articles at exact boundary go to the start of the next bucket", () => {
    const now = 12 * HOUR;
    const items = [
      art(now - HOUR),       // boundary between bucket 10 and 11 → bucket 11
      art(now - 2 * HOUR),   // boundary 9/10 → bucket 10
      art(now - 0.5 * HOUR), // strictly inside bucket 11
    ];
    const out = articlesToBuckets(items, 12, 12 * HOUR, now);
    expect(out).toHaveLength(12);
    expect(out[10]).toBe(1);
    expect(out[11]).toBe(2);
  });

  test("returns an array of length === bucketCount when non-empty", () => {
    const now = 24 * DAY;
    const items = Array.from({ length: 8 }, (_, i) => art(now - (i + 1) * HOUR));
    expect(articlesToBuckets(items, 6, DAY, now)).toHaveLength(6);
    expect(articlesToBuckets(items, 24, DAY, now)).toHaveLength(24);
  });

  test("accepts publishedAt (camelCase) as well as published_at", () => {
    const now = 24 * DAY;
    const items = [
      { publishedAt: new Date(now - HOUR).toISOString() },
      { publishedAt: new Date(now - 2 * HOUR).toISOString() },
      { publishedAt: new Date(now - 3 * HOUR).toISOString() },
    ];
    const out = articlesToBuckets(items, 12, DAY, now);
    expect(out.reduce((a, b) => a + b, 0)).toBe(3);
  });
});
