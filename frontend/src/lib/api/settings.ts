/* path: src/lib/api/settings.ts
   version: 1 */

import { apiClient } from "./client";
import { API_ENDPOINTS } from "../utils/constants";
import type {
  UserSettings,
  UpdateSettingsRequest,
  UpdateSettingsResponse,
} from "@/types/settings";

/**
 * API functions for user settings management
 */
export const settingsApi = {
  /**
   * Get current user settings
   */
  get: async (): Promise<UserSettings> => {
    const response = await apiClient.get<{ settings: UserSettings }>(
      API_ENDPOINTS.SETTINGS,
    );
    return response.settings;
  },

  /**
   * Update user settings
   */
  update: async (data: UpdateSettingsRequest): Promise<UserSettings> => {
    const response = await apiClient.put<UpdateSettingsResponse>(
      API_ENDPOINTS.SETTINGS,
      data,
    );
    return response.settings;
  },
};
