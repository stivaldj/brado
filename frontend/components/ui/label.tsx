import * as React from "react";

import { cn } from "@/lib/utils";

export const Label = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn("mono-label text-sm font-medium leading-none tracking-[0.04em] text-foreground", className)}
      {...props}
    />
  )
);
Label.displayName = "Label";
