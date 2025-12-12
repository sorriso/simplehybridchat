/* path: frontend/src/components/ui/IconButton.tsx
   version: 1 */

import { ButtonHTMLAttributes, forwardRef } from "react";
import { LucideIcon } from "lucide-react";
import clsx from "clsx";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: LucideIcon;
  size?: "sm" | "md" | "lg";
  variant?: "ghost" | "danger";
}

/**
 * Icon-only button component
 */
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    { icon: Icon, size = "md", variant = "ghost", className, ...props },
    ref,
  ) => {
    const iconSizes = {
      sm: 16,
      md: 20,
      lg: 24,
    };

    const buttonSizes = {
      sm: "p-1",
      md: "p-2",
      lg: "p-3",
    };

    return (
      <button
        ref={ref}
        className={clsx(
          "inline-flex items-center justify-center rounded-lg transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          {
            "hover:bg-gray-100 text-gray-600": variant === "ghost",
            "hover:bg-red-100 text-red-600": variant === "danger",
          },
          buttonSizes[size],
          className,
        )}
        {...props}
      >
        <Icon size={iconSizes[size]} />
      </button>
    );
  },
);

IconButton.displayName = "IconButton";
