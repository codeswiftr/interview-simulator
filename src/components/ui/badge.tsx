import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/cn";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        // Core variants
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-muted text-muted-foreground hover:bg-muted/80",
        outline:
          "border-border text-foreground bg-transparent",

        // Status variants - for feedback and states
        success:
          "border-transparent bg-status-success/10 text-status-success",
        warning:
          "border-transparent bg-status-warning/10 text-status-warning",
        error:
          "border-transparent bg-status-error/10 text-status-error",
        info:
          "border-transparent bg-electric-blue/10 text-electric-blue",

        // Session status variants
        scheduled:
          "border-sky-500/20 bg-sky-500/10 text-sky-600 dark:text-sky-400",
        "in-progress":
          "border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400",
        completed:
          "border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",

        // Difficulty variants
        easy:
          "border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
        medium:
          "border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400",
        hard:
          "border-rose-500/20 bg-rose-500/10 text-rose-600 dark:text-rose-400",

        // Category variants
        behavioral:
          "border-purple-500/20 bg-purple-500/10 text-purple-600 dark:text-purple-400",
        technical:
          "border-blue-500/20 bg-blue-500/10 text-blue-600 dark:text-blue-400",
        "system-design":
          "border-cyan-500/20 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400",

        // Brand variant
        brand:
          "border-[#FF6B9D]/20 bg-[#FF6B9D]/10 text-[#FF6B9D]",
      },
      size: {
        default: "px-2.5 py-0.5 text-xs",
        sm: "px-2 py-0.5 text-[10px]",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant, size }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
