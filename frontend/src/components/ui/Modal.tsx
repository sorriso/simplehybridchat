/* path: frontend/src/components/ui/Modal.tsx
   version: 3 - FIXED: Backdrop opacity using inline style instead of Tailwind class */

import { ReactNode, useEffect, useId } from "react";
import { X } from "lucide-react";
import { IconButton } from "./IconButton";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg";
}

/**
 * Modal component with overlay
 * Implements WAI-ARIA dialog pattern for accessibility
 *
 * FIXED v3: Using inline style for backdrop opacity because Tailwind
 * bg-opacity classes may not compile properly in some setups
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
}: ModalProps) {
  const titleId = useId();

  // Close on escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: "max-w-md",
    md: "max-w-lg",
    lg: "max-w-2xl",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay - FIXED: Using inline style for opacity */}
      <div
        className="absolute inset-0"
        style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}
        data-overlay="true"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal content */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        className={`
             relative bg-white rounded-lg shadow-xl
             w-full mx-4 ${sizeClasses[size]}
             max-h-[90vh] overflow-y-auto
           `}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 id={titleId} className="text-xl font-semibold">
              {title}
            </h2>
            <IconButton icon={X} onClick={onClose} aria-label="Close modal" />
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
}
