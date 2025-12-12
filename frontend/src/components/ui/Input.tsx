/* path: frontend/src/components/ui/Input.tsx
   version: 2 */

import { InputHTMLAttributes, forwardRef, useId } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

/**
 * Reusable input component with label and error support
 * Implements proper label association for accessibility
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    { className, label, error, fullWidth = false, id: providedId, ...props },
    ref,
  ) => {
    const generatedId = useId();
    const inputId = providedId || generatedId;
    const errorId = error ? `${inputId}-error` : undefined;

    return (
      <div className={clsx("flex flex-col gap-1", { "w-full": fullWidth })}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={errorId}
          className={clsx(
            "px-3 py-2 border rounded-lg transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
            "disabled:bg-gray-100 disabled:cursor-not-allowed",
            {
              "border-gray-300": !error,
              "border-red-500": error,
            },
            className,
          )}
          {...props}
        />
        {error && (
          <span id={errorId} className="text-sm text-red-600" role="alert">
            {error}
          </span>
        )}
      </div>
    );
  },
);

Input.displayName = "Input";
