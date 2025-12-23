import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/cn";

const cardVariants = cva(
  "rounded-xl border transition-all duration-300",
  {
    variants: {
      variant: {
        // Default - standard card (matches legacy .card)
        default:
          "bg-muted/40 border-border shadow-sm hover:shadow-md",

        // Glass - frosted glass effect
        glass:
          "bg-white/5 dark:bg-white/5 border-white/10 backdrop-blur-sm",

        // Interactive - clickable cards with hover effects (matches legacy .card-interactive)
        interactive:
          "bg-muted/40 border-border shadow-sm cursor-pointer hover:shadow-lg hover:shadow-primary/15 hover:border-primary/40 hover:-translate-y-0.5",

        // Elevated - more prominent cards
        elevated:
          "bg-background border-border shadow-md hover:shadow-lg",

        // Outline - minimal border style
        outline:
          "bg-transparent border-border",

        // Solid - solid background for contrast
        solid:
          "bg-muted border-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(cardVariants({ variant }), className)}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "font-semibold leading-none tracking-tight text-lg",
      className
    )}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  cardVariants,
};
