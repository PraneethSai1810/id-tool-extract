export default function ScannedList({ entries, onRemove }) {
  if (entries.length === 0) {
    return (
      <p className="text-center text-slate/50 text-sm mt-2 py-3">
        No cards scanned yet — tap above to start
      </p>
    );
  }

  return (
    <div className="w-full flex flex-col gap-2 mt-2">
      <p className="text-xs text-slate font-semibold uppercase tracking-wide">
        {entries.length} scanned
      </p>
      {entries.map((entry, idx) => (
        <div
          key={idx}
          className="flex items-center justify-between p-3 bg-paper rounded-lg border border-black/5"
        >
          <div className="flex flex-col">
            <span className="font-medium text-ink text-sm">
              {entry.title} {entry.full_name || `${entry.given_name || ""} ${entry.surname || ""}`.trim()}
            </span>
            <span className="text-xs text-slate">
              {entry.document_type} · {entry.gender || "—"} · {entry.dob || "—"}
            </span>
          </div>
          <button
            onClick={() => onRemove(idx)}
            className="text-stamp-red/70 text-lg px-2 py-1 active:bg-stamp-red/10 rounded-lg"
            aria-label="Remove entry"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}