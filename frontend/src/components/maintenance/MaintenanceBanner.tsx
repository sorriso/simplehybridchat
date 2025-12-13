/* path: frontend/src/components/maintenance/MaintenanceBanner.tsx
   version: 2 - FIXED: Added onDisable prop and AlertTriangle icon to match tests */

import { AlertTriangle, X } from "lucide-react";
import { IconButton } from "../ui/IconButton";
import { Button } from "../ui/Button";

interface MaintenanceBannerProps {
  onDisable: () => void;
  onDismiss?: () => void;
}

/**
 * Banner notification for maintenance mode
 */
export function MaintenanceBanner({
  onDisable,
  onDismiss,
}: MaintenanceBannerProps) {
  return (
    <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-3">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <AlertTriangle
            size={20}
            className="text-yellow-600 flex-shrink-0"
            data-testid="alert-triangle-icon"
          />
          <div>
            <p className="text-sm font-medium text-yellow-800">
              MAINTENANCE MODE ACTIVE
            </p>
            <p className="text-xs text-yellow-700">
              Only root users can access the application. Regular users are
              temporarily blocked.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={onDisable}
            variant="secondary"
            size="sm"
            className="whitespace-nowrap"
          >
            Disable Maintenance Mode
          </Button>
          {onDismiss && (
            <IconButton
              icon={X}
              onClick={onDismiss}
              title="Dismiss banner"
              size="sm"
              variant="ghost"
            />
          )}
        </div>
      </div>
    </div>
  );
}
