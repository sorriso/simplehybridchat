/* path: src/components/maintenance/MaintenanceBanner.tsx
   version: 1 */

import { AlertTriangle, X } from "lucide-react";
import { Button } from "../ui/Button";
import { IconButton } from "../ui/IconButton";

interface MaintenanceBannerProps {
  onDisable: () => void;
  onDismiss?: () => void;
}

/**
 * Warning banner for root users when maintenance mode is active
 * Shows at top of app with option to disable maintenance mode
 */
export function MaintenanceBanner({
  onDisable,
  onDismiss,
}: MaintenanceBannerProps) {
  return (
    <div className="bg-yellow-50 border-b border-yellow-200">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Warning message */}
          <div className="flex items-center gap-3 flex-1">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-900">
                ⚠️ MAINTENANCE MODE ACTIVE
              </p>
              <p className="text-xs text-yellow-700">
                Only root users can access the application. Regular users will
                see the maintenance page.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 ml-4">
            <Button
              variant="secondary"
              size="sm"
              onClick={onDisable}
              className="whitespace-nowrap"
            >
              Disable Maintenance Mode
            </Button>
            {onDismiss && (
              <IconButton
                icon={X}
                size="sm"
                onClick={onDismiss}
                title="Dismiss banner"
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
