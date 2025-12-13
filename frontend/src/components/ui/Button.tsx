/* path: frontend/src/components/ui/Button.tsx
   version: 2 - FIXED: Added fallback inline styles for when Tailwind doesn't compile */

import { ButtonHTMLAttributes, ReactNode } from "react";
import { clsx } from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  children: ReactNode;
}

/**
 * Button component
 *
 * FIXED v2: Added inline style fallbacks for when Tailwind classes don't compile
 * This ensures buttons are always visible and clickable
 */
export function Button({
  variant = "primary",
  size = "md",
  fullWidth = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  // Base styles that work even without Tailwind
  const baseInlineStyle: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 500,
    borderRadius: "0.375rem",
    transition: "all 0.15s",
    cursor: disabled ? "not-allowed" : "pointer",
    border: "none",
    fontFamily: "inherit",
  };

  // Variant-specific inline styles (fallback)
  const variantInlineStyles: Record<string, React.CSSProperties> = {
    primary: {
      backgroundColor: disabled ? "#9ca3af" : "#2563eb",
      color: "#ffffff",
      opacity: disabled ? 0.5 : 1,
    },
    secondary: {
      backgroundColor: disabled ? "#f3f4f6" : "#ffffff",
      color: disabled ? "#9ca3af" : "#374151",
      border: "1px solid #d1d5db",
      opacity: disabled ? 0.5 : 1,
    },
    danger: {
      backgroundColor: disabled ? "#9ca3af" : "#dc2626",
      color: "#ffffff",
      opacity: disabled ? 0.5 : 1,
    },
    ghost: {
      backgroundColor: "transparent",
      color: disabled ? "#9ca3af" : "#374151",
      opacity: disabled ? 0.5 : 1,
    },
  };

  // Size-specific inline styles
  const sizeInlineStyles: Record<string, React.CSSProperties> = {
    sm: {
      padding: "0.375rem 0.75rem",
      fontSize: "0.875rem",
    },
    md: {
      padding: "0.5rem 1rem",
      fontSize: "0.875rem",
    },
    lg: {
      padding: "0.625rem 1.25rem",
      fontSize: "1rem",
    },
  };

  // Combine inline styles
  const combinedInlineStyle: React.CSSProperties = {
    ...baseInlineStyle,
    ...variantInlineStyles[variant],
    ...sizeInlineStyles[size],
    ...(fullWidth ? { width: "100%" } : {}),
  };

  // Tailwind classes (will work when Tailwind compiles)
  const classes = clsx(
    // Base
    "inline-flex items-center justify-center font-medium rounded-md transition-colors",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
    // Variant
    {
      "bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500":
        variant === "primary" && !disabled,
      "bg-white text-gray-900 border border-gray-300 hover:bg-gray-50 focus-visible:ring-primary-500":
        variant === "secondary" && !disabled,
      "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500":
        variant === "danger" && !disabled,
      "text-gray-700 hover:bg-gray-100 focus-visible:ring-gray-500":
        variant === "ghost" && !disabled,
      "opacity-50 cursor-not-allowed": disabled,
    },
    // Size
    {
      "px-3 py-1.5 text-sm": size === "sm",
      "px-4 py-2 text-sm": size === "md",
      "px-5 py-2.5 text-base": size === "lg",
    },
    // Width
    {
      "w-full": fullWidth,
    },
    className,
  );

  return (
    <button
      className={classes}
      style={combinedInlineStyle}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
