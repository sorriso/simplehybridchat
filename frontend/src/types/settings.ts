/* path: src/types/settings.ts
   version: 1 */

/**
 * User settings type
 */
export interface UserSettings {
  id: string;
  userId: string;
  promptCustomization: string;
  theme: "light" | "dark" | "auto";
  language: string;
  updatedAt: Date;
}

export interface UpdateSettingsRequest {
  promptCustomization?: string;
  theme?: "light" | "dark" | "auto";
  language?: string;
}

export interface UpdateSettingsResponse {
  settings: UserSettings;
  message: string;
}

// Default settings for new users
export const DEFAULT_SETTINGS: Omit<
  UserSettings,
  "id" | "userId" | "updatedAt"
> = {
  promptCustomization: "",
  theme: "auto",
  language: "en",
};
