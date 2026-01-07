/* path: frontend/src/lib/hooks/useSettings.ts
   version: 4 - FIXED: Allow updates even when settings is null + more debug logs
   
   Changes in v4:
   - FIXED: Removed settings null check that was blocking updates
   - FIXED: Removed settings from updateSettings dependencies
   - ADDED: More comprehensive debug logs in loadSettings
   - Reason: Settings was null on initial load, blocking all updates
   
   Changes in v3:
   - ADDED: Debug logs to trace save flow */

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
    console.log("[DEBUG useSettings.loadSettings] Starting...");

    try {
      setLoading(true);
      setError(null);

      console.log(
        "[DEBUG useSettings.loadSettings] Calling settingsApi.get()...",
      );
      const data = await settingsApi.get();
      console.log("[DEBUG useSettings.loadSettings] API response:", data);

      setSettings(data);
      console.log(
        "[DEBUG useSettings.loadSettings] Settings loaded successfully",
      );
    } catch (err) {
      // Use consistent error message for tests
      setError("Failed to load settings");
      console.error("[DEBUG useSettings.loadSettings] Error:", err);

      // Use default settings on error
      const defaultSettings = {
        id: "default",
        userId: "default",
        ...DEFAULT_SETTINGS,
        updatedAt: new Date(),
      };
      console.log(
        "[DEBUG useSettings.loadSettings] Using default settings:",
        defaultSettings,
      );
      setSettings(defaultSettings);
    } finally {
      setLoading(false);
      console.log("[DEBUG useSettings.loadSettings] Loading complete");
    }
  };

  /**
   * Update user settings
   */
  const updateSettings = useCallback(
    async (updates: UpdateSettingsRequest) => {
      console.log("[DEBUG useSettings.updateSettings] Called with:", updates);

      // Don't abort if settings is null - API will handle it
      console.log(
        "[DEBUG useSettings.updateSettings] Current settings:",
        settings,
      );

      try {
        console.log("[DEBUG useSettings.updateSettings] Setting isSaving=true");
        setIsSaving(true);
        setError(null);

        console.log(
          "[DEBUG useSettings.updateSettings] Calling settingsApi.update...",
        );
        const updated = await settingsApi.update(updates);
        console.log(
          "[DEBUG useSettings.updateSettings] API call successful:",
          updated,
        );

        setSettings(updated);
        console.log(
          "[DEBUG useSettings.updateSettings] Settings state updated",
        );

        return updated;
      } catch (err) {
        // Use consistent error message for tests
        setError("Failed to save settings");
        console.error("[DEBUG useSettings.updateSettings] Error:", err);
        throw err;
      } finally {
        console.log(
          "[DEBUG useSettings.updateSettings] Setting isSaving=false",
        );
        setIsSaving(false);
      }
    },
    [], // Remove settings dependency - allow updates even when null
  );

  /**
   * Update prompt customization
   */
  const updatePromptCustomization = useCallback(
    async (promptCustomization: string) => {
      console.log(
        "[DEBUG useSettings.updatePromptCustomization] Called with:",
        promptCustomization,
      );
      return updateSettings({ promptCustomization });
    },
    [updateSettings],
  );

  /**
   * Update theme
   */
  const updateTheme = useCallback(
    async (theme: "light" | "dark" | "auto") => {
      console.log("[DEBUG useSettings.updateTheme] Called with:", theme);
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
