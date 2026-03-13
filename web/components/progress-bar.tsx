function clamp(value: number) {
  return Math.max(0, Math.min(100, value));
}

export function ProgressBar({
  value,
  tone = "sky",
  label = "流程进度",
  helper,
}: {
  value: number;
  tone?: "sky" | "emerald" | "amber" | "rose";
  label?: string;
  helper?: string;
}) {
  const normalized = clamp(value);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3 text-xs text-slate-400">
        <span>{label}</span>
        <span>{Math.round(normalized)}%</span>
      </div>

      <div
        className="progress-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(normalized)}
        aria-valuetext={`${Math.round(normalized)}%`}
      >
        <div
          className={`progress-fill progress-fill--${tone}`}
          style={{
            width: `${normalized}%`,
          }}
        />
      </div>

      {helper ? <p className="text-xs leading-5 text-slate-400">{helper}</p> : null}
    </div>
  );
}
