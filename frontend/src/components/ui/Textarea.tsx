import React from "react";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  helperText,
  id,
  className = "",
  rows = 4,
  ...props
}) => {
  const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label htmlFor={textareaId} className="block text-xs font-medium text-zinc-300">
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        rows={rows}
        className={`w-full rounded-lg border bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50 ${
          error ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500" : "border-zinc-800"
        } ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-rose-400">{error}</p>}
      {helperText && !error && <p className="text-xs text-zinc-500">{helperText}</p>}
    </div>
  );
};

