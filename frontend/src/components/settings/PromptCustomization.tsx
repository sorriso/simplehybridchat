/* path: src/components/settings/PromptCustomization.tsx
   version: 1 */

import { useState, useEffect } from "react";
import { Save } from "lucide-react";
import { Button } from "../ui/Button";

interface PromptCustomizationProps {
  initialValue: string;
  onSave: (value: string) => Promise<void>;
  isSaving: boolean;
}

/**
 * Component to edit and save prompt customization
 */
export function PromptCustomization({
  initialValue,
  onSave,
  isSaving,
}: PromptCustomizationProps) {
  const [value, setValue] = useState(initialValue);
  const [hasChanges, setHasChanges] = useState(false);

  // Update local state when initial value changes
  useEffect(() => {
    setValue(initialValue);
    setHasChanges(false);
  }, [initialValue]);

  // Track changes
  const handleChange = (newValue: string) => {
    setValue(newValue);
    setHasChanges(newValue !== initialValue);
  };

  // Handle save
  const handleSave = async () => {
    if (!hasChanges) return;

    try {
      await onSave(value);
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save prompt customization:", error);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Prompt Customization
        </label>
        <p className="text-sm text-gray-500 mb-3">
          Add custom instructions to personalize how the AI responds to you.
          These instructions will be included in every conversation.
        </p>
        <textarea
          value={value}
          onChange={(e) => handleChange(e.target.value)}
          placeholder="Example: Always respond in a professional tone and provide detailed explanations..."
          rows={8}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none
                     focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-400 mt-1">{value.length} characters</p>
      </div>

      <div className="flex items-center justify-between">
        <div>
          {hasChanges && (
            <span className="text-sm text-orange-600">Unsaved changes</span>
          )}
        </div>
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          className="flex items-center gap-2"
        >
          <Save size={16} />
          {isSaving ? "Saving..." : "Save Changes"}
        </Button>
      </div>
    </div>
  );
}
