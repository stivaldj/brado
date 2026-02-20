import React from 'react';

export const Separator = ({ orientation = "horizontal", className = "" }: { orientation?: "horizontal" | "vertical"; className?: string }) => {
  const classes = orientation === "vertical" ? `w-px h-full bg-gray-200 ${className}` : `h-px w-full bg-gray-200 ${className}`;
  return <div className={classes} />;
};
