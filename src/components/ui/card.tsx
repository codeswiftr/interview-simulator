import * as React from "react";
import { cn } from "../../lib/cn";

export function Card(props: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={cn(
        "rounded-lg border border-border bg-muted/40 p-4 shadow-sm",
        props.className
      )}
    />
  );
}

export function CardHeader(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return (
    <div
      {...props}
      className={cn(
        "mb-2 flex items-center justify-between gap-2 text-sm font-medium text-muted-foreground",
        props.className
      )}
    />
  );
}

export function CardTitle(
  props: React.HTMLAttributes<HTMLHeadingElement>
) {
  return (
    <h3
      {...props}
      className={cn(
        "text-base font-semibold text-foreground",
        props.className
      )}
    />
  );
}

export function CardContent(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return (
    <div
      {...props}
      className={cn("text-sm text-muted-foreground", props.className)}
    />
  );
}
