import React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "subtle" | "highlight" | "danger";
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = "default",
  className = "",
  ...props
}) => {
  const variantClasses = {
    default: "bg-zinc-900/90 border-zinc-800 text-zinc-100",
    subtle: "bg-zinc-900/40 border-zinc-800/60 text-zinc-300",
    highlight: "bg-indigo-950/20 border-indigo-500/30 text-zinc-100 shadow-indigo-950/20",
    danger: "bg-rose-950/20 border-rose-500/30 text-zinc-100",
  };

  return (
    <div
      className={`rounded-xl border p-5 shadow-sm transition-all ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = "",
  ...props
}) => (
  <div className={`mb-4 flex flex-col space-y-1.5 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className = "",
  ...props
}) => (
  <h3 className={`text-lg font-semibold leading-none tracking-tight text-zinc-100 ${className}`} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className = "",
  ...props
}) => (
  <p className={`text-sm text-zinc-400 ${className}`} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = "",
  ...props
}) => (
  <div className={`space-y-3 ${className}`} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = "",
  ...props
}) => (
  <div className={`mt-5 flex items-center justify-between pt-3 border-t border-zinc-800/80 ${className}`} {...props}>
    {children}
  </div>
);

