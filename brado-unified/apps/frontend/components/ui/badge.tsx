import React from 'react';

export const Badge = ({ children, variant = "secondary", className = "" }: { children: React.ReactNode; variant?: string; className?: string }) => {
  const base = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";
  const variants: Record<string, string> = {
    primary: "bg-primary text-primary-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    destructive: "bg-destructive text-destructive-foreground",
    outline: "border border-input",
  };
  const variantClass = variants[variant] || variants["secondary"]; 
  return <span className={`${base} ${variantClass} ${className}`}>{children}</span>;
};
