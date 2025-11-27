// path: tests/mocks/server.ts
// version: 3 - MSW v1 syntax with server-instance registration

import { setupServer } from 'msw/node'
import { setServerInstance } from './server-instance'
import { authHandlers } from './handlers/auth'
import { conversationsHandlers } from './handlers/conversations'
import { filesHandlers } from './handlers/files'
import { usersHandlers } from './handlers/users'
import { settingsHandlers } from './handlers/settings'

/**
 * MSW server with all API handlers - MSW v1 syntax
 */
export const server = setupServer(
  ...authHandlers,
  ...conversationsHandlers,
  ...filesHandlers,
  ...usersHandlers,
  ...settingsHandlers
)

// Register server instance for scenarios to use
setServerInstance(server)