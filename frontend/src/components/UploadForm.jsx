import { useRef } from "react";

export default function UploadForm({ onFileSelected, disabled }) {
  const inputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (!selected) return;
    onFileSelected(selected);
    e.target.value = "";
  };

  return (
    <div className="w-full">
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.pdf"
        onChange={handleFileChange}
        className="hidden"
      />

      <button
  onClick={() => inputRef.current.click()}
  disabled={disabled}
  className="w-full py-6 px-4 text-lg font-medium rounded-xl border-2 border-dashed border-passport/40 text-passport active:bg-passport/5 disabled:border-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
>
  {disabled ? "Processing..." : "+ Scan / Upload Next ID"}
</button>

<p className="text-sm text-slate/60 text-center mt-2">
  Accepts JPG, PNG, WEBP, HEIC, or PDF
</p>
    </div>
  );
}