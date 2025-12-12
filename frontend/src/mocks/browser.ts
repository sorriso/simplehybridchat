// path: frontend/src/mocks/browser.ts
// version: 4 - WITH SSE handlers imported

import { setupWorker } from "msw";
import { authHandlers } from "../../tests/mocks/handlers/auth";
import { conversationsHandlers } from "../../tests/mocks/handlers/conversations";
import { filesHandlers } from "../../tests/mocks/handlers/files";
import { usersHandlers } from "../../tests/mocks/handlers/users";
import { settingsHandlers } from "../../tests/mocks/handlers/settings";
import { sseHandlers } from "../../tests/mocks/handlers/sse";

export const worker = setupWorker(
  ...authHandlers,
  ...conversationsHandlers,
  ...filesHandlers,
  ...usersHandlers,
  ...settingsHandlers,
  ...sseHandlers,
);
