type Article = {
  published_at?: string;
  publishedAt?: string;
};

const DEFAULT_WINDOW_MS = 24 * 60 * 60 * 1000;
const MIN_ARTICLES = 3;

function articleTime(a: Article): number | null {
  const raw = a.published_at ?? a.publishedAt;
  if (!raw) return null;
  const t = Date.parse(raw);
  return Number.isFinite(t) ? t : null;
}

/**
 * Bucket articles by publish time into `bucketCount` equal-width buckets ending at `now`.
 * Returns an empty array when the input has fewer than 3 valid articles in the window.
 *
 * Boundary rule: bucket k covers [now - (bucketCount - k) * size, now - (bucketCount - k - 1) * size).
 * An article at exactly a boundary lands in the bucket whose interval starts there.
 */
export function articlesToBuckets(
  articles: Article[],
  bucketCount = 12,
  windowMs: number = DEFAULT_WINDOW_MS,
  now: number = Date.now(),
): number[] {
  if (!articles || articles.length === 0) return [];
  if (bucketCount <= 0) return [];

  const start = now - windowMs;
  const inWindow = articles
    .map(articleTime)
    .filter((t): t is number => t !== null && t >= start && t <= now);

  if (inWindow.length < MIN_ARTICLES) return [];

  const size = windowMs / bucketCount;
  const buckets = new Array<number>(bucketCount).fill(0);
  for (const t of inWindow) {
    const idx = Math.min(bucketCount - 1, Math.floor((t - start) / size));
    buckets[idx] += 1;
  }
  return buckets;
}
