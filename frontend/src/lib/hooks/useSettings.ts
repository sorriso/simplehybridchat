/* path: src/lib/hooks/useSettings.ts
   version: 2 */

import { useState, useEffect, useCallback } from "react";
import { settingsApi } from "../api/settings";
import type { UserSettings, UpdateSettingsRequest } from "@/types/settings";
import { DEFAULT_SETTINGS } from "@/types/settings";

/**
 * Hook for managing user settings
 */
export function useSettings() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  /**
   * Load user settings from API
   */
  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await settingsApi.get();
      setSettings(data);
    } catch (err) {
      // Use consistent error message for tests
      setError("Failed to load settings");
      console.error("Error loading settings:", err);

      // Use default settings on error
      setSettings({
        id: "default",
        userId: "default",
        ...DEFAULT_SETTINGS,
        updatedAt: new Date(),
      });
    } finally {
      setLoading(false);
    }
  };

  /**
   * Update user settings
   */
  const updateSettings = useCallback(
    async (updates: UpdateSettingsRequest) => {
      if (!settings) return;

      try {
        setIsSaving(true);
        setError(null);

        const updated = await settingsApi.update(updates);
        setSettings(updated);

        return updated;
      } catch (err) {
        // Use consistent error message for tests
        setError("Failed to save settings");
        console.error("Error updating settings:", err);
        throw err;
      } finally {
        setIsSaving(false);
      }
    },
    [settings],
  );

  /**
   * Update prompt customization
   */
  const updatePromptCustomization = useCallback(
    async (promptCustomization: string) => {
      return updateSettings({ promptCustomization });
    },
    [updateSettings],
  );

  /**
   * Update theme
   */
  const updateTheme = useCallback(
    async (theme: "light" | "dark" | "auto") => {
      return updateSettings({ theme });
    },
    [updateSettings],
  );

  return {
    // State
    settings,
    loading,
    error,
    isSaving,

    // Actions
    updateSettings,
    updatePromptCustomization,
    updateTheme,
    reload: loadSettings,
  };
}
