import React from "react";

export interface BadgeProps {
  children: React.ReactNode;
  variant?:
    | "default"
    | "primary"
    | "success"
    | "warning"
    | "danger"
    | "info"
    | "github"
    | "x"
    | "linkedin";
  size?: "sm" | "md";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  size = "md",
  className = "",
}) => {
  const baseClasses = "inline-flex items-center font-medium rounded-full border";

  const sizeClasses = {
    sm: "px-2 py-0.5 text-[11px]",
    md: "px-2.5 py-1 text-xs",
  };

  const variantClasses = {
    default: "bg-zinc-800 text-zinc-300 border-zinc-700",
    primary: "bg-indigo-950/80 text-indigo-300 border-indigo-700/60",
    success: "bg-emerald-950/80 text-emerald-300 border-emerald-700/60",
    warning: "bg-amber-950/80 text-amber-300 border-amber-700/60",
    danger: "bg-rose-950/80 text-rose-300 border-rose-700/60",
    info: "bg-sky-950/80 text-sky-300 border-sky-700/60",
    github: "bg-zinc-900 text-zinc-100 border-zinc-600",
    x: "bg-black text-white border-zinc-700",
    linkedin: "bg-blue-950/80 text-blue-300 border-blue-700/60",
  };

  return (
    <span className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
};

