type Props = {
  buckets: number[];
};

export default function ActivitySparkline({ buckets }: Props) {
  if (buckets.length === 0) return null;
  const max = Math.max(...buckets, 1);

  return (
    <div className="flex items-end gap-0.5" style={{ height: 18 }}>
      {buckets.map((h, i) => (
        <div
          key={i}
          className="flex-1 rounded-sm"
          style={{
            height: `${(h / max) * 100}%`,
            background: "var(--accent)",
            opacity: 0.35 + i / 22,
          }}
        />
      ))}
    </div>
  );
}
