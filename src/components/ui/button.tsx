import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        // Primary - matches .btn-primary
        default:
          "bg-primary text-primary-foreground shadow-md shadow-primary/25 hover:opacity-90 hover:shadow-lg hover:shadow-primary/35 hover:-translate-y-0.5 active:translate-y-0",

        // Secondary - matches .btn-secondary
        secondary:
          "bg-background text-foreground border border-border shadow-sm hover:bg-muted hover:-translate-y-0.5 hover:shadow-md active:translate-y-0",

        // Outline - minimal border style
        outline:
          "border border-border bg-transparent hover:bg-muted",

        // Ghost - matches .btn-ghost
        ghost:
          "bg-transparent text-muted-foreground hover:bg-primary/10 hover:text-primary active:scale-[0.98]",

        // Subtle - muted background
        subtle:
          "bg-muted text-muted-foreground hover:bg-muted/80",

        // Destructive - for danger/error actions
        destructive:
          "bg-status-error text-white shadow-md shadow-red-500/25 hover:opacity-90 hover:shadow-lg hover:shadow-red-500/35",

        // Success - for positive actions
        success:
          "bg-status-success text-white shadow-md shadow-emerald-500/25 hover:opacity-90 hover:shadow-lg hover:shadow-emerald-500/35",
      },
      size: {
        default: "h-10 px-6 py-2",
        sm: "h-9 px-4 py-1.5 text-xs",
        lg: "h-12 px-8 py-3 text-base",
        icon: "h-10 w-10",
        fab: "h-14 w-14 rounded-full shadow-lg",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
