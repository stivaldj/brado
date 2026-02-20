"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface SliderProps {
  value?: number[];
  defaultValue?: number[];
  min?: number;
  max?: number;
  step?: number;
  className?: string;
  onValueChange?: (value: number[]) => void;
}

export function Slider({
  value,
  defaultValue = [0],
  min = 0,
  max = 100,
  step = 1,
  className,
  onValueChange,
}: SliderProps) {
  const resolved = value?.[0] ?? defaultValue[0] ?? 0;

  return (
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={resolved}
      onChange={(event) => onValueChange?.([Number(event.target.value)])}
      className={cn("h-2 w-full cursor-pointer appearance-none rounded-lg bg-muted", className)}
      aria-label="Slider"
    />
  );
}
