import * as React from "react";
import { cn } from "../../lib/cn";

interface FieldContextValue {
  id: string;
  error?: string;
}

const FieldContext = React.createContext<FieldContextValue | undefined>(undefined);

function useFieldContext() {
  const context = React.useContext(FieldContext);
  if (!context) {
    throw new Error("Field components must be used within a Field");
  }
  return context;
}

export interface FieldProps extends React.HTMLAttributes<HTMLDivElement> {
  error?: string;
}

const Field = React.forwardRef<HTMLDivElement, FieldProps>(
  ({ className, error, children, ...props }, ref) => {
    const id = React.useId();

    return (
      <FieldContext.Provider value={{ id, error }}>
        <div
          ref={ref}
          className={cn("space-y-2", className)}
          {...props}
        >
          {children}
        </div>
      </FieldContext.Provider>
    );
  }
);
Field.displayName = "Field";

export interface FieldLabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {}

const FieldLabel = React.forwardRef<HTMLLabelElement, FieldLabelProps>(
  ({ className, ...props }, ref) => {
    const { id, error } = useFieldContext();

    return (
      <label
        ref={ref}
        htmlFor={id}
        className={cn(
          "block text-sm font-medium text-foreground",
          error && "text-status-error",
          className
        )}
        {...props}
      />
    );
  }
);
FieldLabel.displayName = "FieldLabel";

export interface FieldInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const FieldInput = React.forwardRef<HTMLInputElement, FieldInputProps>(
  ({ className, ...props }, ref) => {
    const { id, error } = useFieldContext();

    return (
      <input
        ref={ref}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        className={cn(
          "flex h-10 w-full rounded-xl border bg-input px-4 py-2 text-sm transition-all",
          "ring-offset-background placeholder:text-muted-foreground/70",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          error
            ? "border-status-error focus-visible:ring-status-error/50"
            : "border-border",
          className
        )}
        {...props}
      />
    );
  }
);
FieldInput.displayName = "FieldInput";

export interface FieldTextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const FieldTextarea = React.forwardRef<HTMLTextAreaElement, FieldTextareaProps>(
  ({ className, ...props }, ref) => {
    const { id, error } = useFieldContext();

    return (
      <textarea
        ref={ref}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        className={cn(
          "flex min-h-[80px] w-full rounded-xl border bg-input px-4 py-2 text-sm transition-all",
          "ring-offset-background placeholder:text-muted-foreground/70",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          error
            ? "border-status-error focus-visible:ring-status-error/50"
            : "border-border",
          className
        )}
        {...props}
      />
    );
  }
);
FieldTextarea.displayName = "FieldTextarea";

export interface FieldSelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {}

const FieldSelect = React.forwardRef<HTMLSelectElement, FieldSelectProps>(
  ({ className, children, ...props }, ref) => {
    const { id, error } = useFieldContext();

    return (
      <select
        ref={ref}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        className={cn(
          "flex h-10 w-full rounded-xl border bg-input px-4 py-2 text-sm transition-all",
          "ring-offset-background",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          error
            ? "border-status-error focus-visible:ring-status-error/50"
            : "border-border",
          className
        )}
        {...props}
      >
        {children}
      </select>
    );
  }
);
FieldSelect.displayName = "FieldSelect";

export interface FieldDescriptionProps
  extends React.HTMLAttributes<HTMLParagraphElement> {}

const FieldDescription = React.forwardRef<
  HTMLParagraphElement,
  FieldDescriptionProps
>(({ className, ...props }, ref) => {
  return (
    <p
      ref={ref}
      className={cn("text-xs text-muted-foreground", className)}
      {...props}
    />
  );
});
FieldDescription.displayName = "FieldDescription";

export interface FieldErrorProps
  extends React.HTMLAttributes<HTMLParagraphElement> {}

const FieldError = React.forwardRef<HTMLParagraphElement, FieldErrorProps>(
  ({ className, children, ...props }, ref) => {
    const { id, error } = useFieldContext();
    const message = children || error;

    if (!message) return null;

    return (
      <p
        ref={ref}
        id={`${id}-error`}
        role="alert"
        className={cn("text-xs text-status-error font-medium", className)}
        {...props}
      >
        {message}
      </p>
    );
  }
);
FieldError.displayName = "FieldError";

export {
  Field,
  FieldLabel,
  FieldInput,
  FieldTextarea,
  FieldSelect,
  FieldDescription,
  FieldError,
};
