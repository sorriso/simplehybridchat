/* path: frontend/src/lib/api/settings.ts
   version: 2
   
   Changes in v2:
   - FIX: Changed response.settings to response.data (backend uses SuccessResponse)
   - Backend returns {data: UserSettings} not {settings: UserSettings}
   - Matches user_settings.py v2 which returns SuccessResponse(data=...) */

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
       const response = await apiClient.get<{ data: UserSettings }>(
         API_ENDPOINTS.SETTINGS,
       );
       return response.data;
     },
   
     /**
      * Update user settings
      */
     update: async (data: UpdateSettingsRequest): Promise<UserSettings> => {
       const response = await apiClient.put<{ data: UserSettings }>(
         API_ENDPOINTS.SETTINGS,
         data,
       );
       return response.data;
     },
   };