/* path: frontend/src/components/maintenance/MaintenancePage.tsx
   version: 1 */

import { Wrench } from "lucide-react";

/**
 * Full-page maintenance mode screen
 */
export function MaintenancePage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
            <Wrench className="w-10 h-10 text-blue-600" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Application Under Maintenance
        </h1>

        {/* Message */}
        <p className="text-lg text-gray-600 mb-8">
          We're making improvements to better serve you. Please try again later.
        </p>

        {/* Contact Info */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500 mb-2">
            Need immediate assistance?
          </p>
          <a
            href="mailto:support@company.com"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            support@company.com
          </a>
        </div>

        {/* Additional info */}
        <p className="text-xs text-gray-400 mt-8">
          Maintenance is usually completed within a few hours. We appreciate
          your patience.
        </p>
      </div>
    </div>
  );
}
