/* path: frontend/src/components/ui/ContextMenu.tsx
   version: 2 */

import { ReactNode, useEffect, useRef, useState, useCallback } from "react";

interface ContextMenuItem {
  label: string;
  onClick: () => void;
  icon?: ReactNode;
  variant?: "default" | "danger";
}

interface ContextMenuProps {
  items: ContextMenuItem[];
  children: ReactNode;
}

/**
 * Context menu component (right-click menu)
 * Supports keyboard navigation for accessibility
 */
export function ContextMenu({ items, children }: ContextMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [focusedIndex, setFocusedIndex] = useState(0);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Handle context menu open
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setPosition({ x: e.clientX, y: e.clientY });
    setIsOpen(true);
    setFocusedIndex(0);
  };

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setFocusedIndex((prev) => (prev + 1) % items.length);
          break;
        case "ArrowUp":
          e.preventDefault();
          setFocusedIndex((prev) => (prev - 1 + items.length) % items.length);
          break;
        case "Enter":
        case " ":
          e.preventDefault();
          if (items[focusedIndex]) {
            items[focusedIndex].onClick();
            setIsOpen(false);
          }
          break;
        case "Escape":
          e.preventDefault();
          setIsOpen(false);
          break;
      }
    },
    [isOpen, items, focusedIndex],
  );

  // Focus the correct button when focusedIndex changes
  useEffect(() => {
    if (isOpen && buttonRefs.current[focusedIndex]) {
      buttonRefs.current[focusedIndex]?.focus();
    }
  }, [isOpen, focusedIndex]);

  // Close menu when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = () => setIsOpen(false);
    document.addEventListener("click", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("click", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, handleKeyDown]);

  return (
    <>
      <div onContextMenu={handleContextMenu}>{children}</div>

      {isOpen && (
        <div
          ref={menuRef}
          role="menu"
          className="fixed z-50 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[160px]"
          style={{
            left: `${position.x}px`,
            top: `${position.y}px`,
          }}
        >
          {items.map((item, index) => (
            <button
              key={index}
              ref={(el) => {
                buttonRefs.current[index] = el;
              }}
              role="menuitem"
              tabIndex={focusedIndex === index ? 0 : -1}
              onClick={() => {
                item.onClick();
                setIsOpen(false);
              }}
              className={`
                w-full px-4 py-2 text-left text-sm flex items-center gap-2
                transition-colors focus:outline-none focus:bg-gray-100
                ${
                  item.variant === "danger"
                    ? "text-red-600 hover:bg-red-50 focus:bg-red-50"
                    : "text-gray-700 hover:bg-gray-100"
                }
              `}
            >
              {item.icon && <span className="w-4 h-4">{item.icon}</span>}
              <span className={item.variant === "danger" ? "text-red-600" : ""}>
                {item.label}
              </span>
            </button>
          ))}
        </div>
      )}
    </>
  );
}
