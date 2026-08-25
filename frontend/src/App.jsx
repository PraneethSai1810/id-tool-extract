import { useState } from "react";
import UploadForm from "./components/UploadForm";
import ScannedList from "./components/ScannedList";
import { startGroup, finishGroup, extractIdDetails, getDownloadUrl } from "./api";

function App() {
  // Basic password gate for private testing
  const [authenticated, setAuthenticated] = useState(
    sessionStorage.getItem("idscan_authenticated") === "true"
  );
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [passwordError, setPasswordError] = useState(false);

  const APP_PASSWORD = "NSVR@AnilKumar2026";

  const [tripId, setTripId] = useState(null);
  const [entries, setEntries] = useState([]);
  const [startingGroup, setStartingGroup] = useState(false);
  const [showWakeMessage, setShowWakeMessage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastFinishedTripId, setLastFinishedTripId] = useState(null);
  const [lastFinishedCount, setLastFinishedCount] = useState(0);

  const handleLogin = (e) => {
    e.preventDefault();

    if (password === APP_PASSWORD) {
      sessionStorage.setItem("idscan_authenticated", "true");
      setAuthenticated(true);
      setPassword("");
      setPasswordError(false);
    } else {
      setPasswordError(true);
    }
  };

 const handleStartGroup = async () => {
  setError(null);
  setLastFinishedTripId(null);
  setStartingGroup(true);
  setShowWakeMessage(false);

  // If the request takes more than 3 seconds,
  // Render is probably waking up from inactivity
  const wakeTimer = setTimeout(() => {
    setShowWakeMessage(true);
  }, 3000);

  try {
    const data = await startGroup();

    setTripId(data.trip_id);
    setEntries([]);

  } catch (err) {
    setError("Couldn't start a new group. Check your connection and try again.");
    console.error(err);

  } finally {
    clearTimeout(wakeTimer);
    setStartingGroup(false);
    setShowWakeMessage(false);
  }
};

  const handleFileSelected = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const data = await extractIdDetails(file, tripId);
      setEntries((prev) => [...prev, data]);
    } catch (err) {
      const message = err.message?.includes("502")
        ? "Couldn't read that ID clearly — try a sharper photo or better lighting."
        : err.message?.includes("Failed to fetch")
        ? "Connection issue — check your internet and try again."
        : "That scan failed. Try uploading it again.";
      setError(message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = (idx) => {
    setEntries((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleFinishGroup = async () => {
    if (entries.length === 0 || loading) return;
    setError(null);

    try {
      await finishGroup(tripId);
      setLastFinishedTripId(tripId);
      setLastFinishedCount(entries.length);
      setTripId(null);
      setEntries([]);
    } catch (err) {
      setError("Couldn't finish the group. Try again.");
      console.error(err);
    }
  };

  // Password screen
  if (!authenticated) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-white rounded-2xl border border-black/5 shadow-sm p-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center gap-2 mb-3">
              <div className="w-12 h-12 rounded-md bg-ink flex items-center justify-center">
                <span
                  className="text-paper text-lg font-bold"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  ID
                </span>
              </div>
            </div>

            <h1
              className="text-3xl font-bold text-ink"
              style={{ fontFamily: "var(--font-display)" }}
            >
              ID Scan
            </h1>

            <p className="text-slate mt-2">
              Enter password to continue
            </p>
          </div>

          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <div className="relative">
  <input
    type={showPassword ? "text" : "password"}
    value={password}
    onChange={(e) => {
      setPassword(e.target.value);
      setPasswordError(false);
    }}
    placeholder="Enter password"
    className="w-full px-4 py-3 pr-12 border border-black/10 rounded-xl outline-none"
    autoFocus
  />

  <button
    type="button"
    onClick={() => setShowPassword(!showPassword)}
    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate"
    aria-label={showPassword ? "Hide password" : "Show password"}
  >
    {showPassword ? (
      <svg
        className="w-5 h-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 3l18 18"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M10.6 10.6a3 3 0 004.24 4.24"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9.88 4.24A10.94 10.94 0 0112 4c5 0 9.27 3.11 11 7.5"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M6.61 6.61A11.83 11.83 0 001 11.5C2.73 15.89 7 19 12 19"
        />
      </svg>
    ) : (
      <svg
        className="w-5 h-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"
        />
        <circle cx="12" cy="12" r="3" />
      </svg>
    )}
  </button>
</div>

            {passwordError && (
              <p className="text-stamp-red text-sm text-center">
                Incorrect password
              </p>
            )}

            <button
              type="submit"
              className="w-full py-4 text-lg font-semibold rounded-xl bg-passport text-white shadow-sm active:bg-ink active:scale-[0.98] transition-all"
            >
              Continue
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper flex flex-col items-center justify-center py-10 px-4">
      <div className="w-full max-w-sm">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
            <div className="w-12 h-12 rounded-md bg-ink flex items-center justify-center">
              <span
                className="text-paper text-lg font-bold"
                style={{ fontFamily: "var(--font-display)" }}
              >
                ID
              </span>
            </div>
          </div>

          <h1
            className="text-4xl font-bold text-ink"
            style={{ fontFamily: "var(--font-display)" }}
          >
            ID Scan
          </h1>

          <p className="text-lg text-slate mt-2">
            Auto-extract details from ID cards
          </p>
        </div>

        {/* Main card */}
        <div className="bg-white rounded-2xl border border-black/5 shadow-sm p-6">
          {!tripId ? (
            <div className="flex flex-col gap-3">
  <button
    onClick={handleStartGroup}
    disabled={startingGroup}
    className="w-full py-4 text-lg font-semibold rounded-xl bg-passport text-white shadow-sm active:bg-ink active:scale-[0.98] transition-all disabled:opacity-70 min-h-14"
  >
    {startingGroup ? (
      <span className="flex items-center justify-center gap-2">
        <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
        Starting...
      </span>
    ) : (
      "Start New Group"
    )}
  </button>

  {showWakeMessage && (
    <div className="text-center px-3 py-2">
      <p className="text-passport font-medium">
        Server is starting up...
      </p>

      <p className="text-sm text-slate mt-1">
        The service was inactive and may take up to a minute to wake up.
        Please wait.
      </p>
    </div>
  )}
</div>
          ) : (
            <div className="flex flex-col gap-4">
              <UploadForm
                onFileSelected={handleFileSelected}
                disabled={loading}
              />

              {loading && (
                <div className="flex items-center justify-center gap-2 py-2">
                  <div className="w-5 h-5 border-2 border-passport border-t-transparent rounded-full animate-spin" />
                  <p className="text-passport text-base font-medium">
                    Reading ID details...
                  </p>
                </div>
              )}

              <ScannedList
                entries={entries}
                onRemove={handleRemove}
              />

              <button
                onClick={handleFinishGroup}
                disabled={entries.length === 0 || loading}
                className="w-full py-4 text-lg font-semibold rounded-xl bg-stamp text-white shadow-sm active:bg-emerald-800 active:scale-[0.98] transition-all disabled:bg-gray-200 disabled:text-gray-400 disabled:shadow-none min-h-14 mt-1"
              >
                Finish Group
                {entries.length > 0 ? ` (${entries.length})` : ""}
              </button>
            </div>
          )}
        </div>

        {/* Success / download */}
        {lastFinishedTripId && (
          <div className="mt-6 flex flex-col items-center gap-2 p-5 bg-white border-2 border-dashed border-stamp/40 rounded-xl relative overflow-hidden">
            <div className="w-12 h-12 rounded-full bg-stamp/10 flex items-center justify-center mb-1">
              <svg
                className="w-6 h-6 text-stamp"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>

            <p className="text-ink text-base font-semibold text-center">
              Group closed — {lastFinishedCount}{" "}
              {lastFinishedCount === 1 ? "person" : "people"} scanned
            </p>

            <a
              href={getDownloadUrl(lastFinishedTripId)}
              className="text-base font-semibold text-passport underline underline-offset-2"
            >
              Download CSV
            </a>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 p-4 bg-white border border-stamp-red/30 rounded-xl">
            <p className="text-base text-stamp-red font-medium text-center">
              {error}
            </p>
          </div>
        )}

        <p className="text-sm text-slate text-center mt-8 px-2 leading-relaxed">
          ID details are processed securely to speed up your booking. Photos
          are not stored — extracted data is used only for this booking and
          removed automatically after download.
        </p>
      </div>
    </div>
  );
}

export default App;