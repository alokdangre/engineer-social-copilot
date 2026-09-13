import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  id,
  className = "",
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label htmlFor={inputId} className="block text-xs font-medium text-zinc-300">
          {label}
        </label>
      )}
      <input
        id={inputId}
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

