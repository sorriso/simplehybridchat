// path: tests/mocks/server-instance.ts
// version: 1

import { SetupServer } from 'msw/node'

/**
 * Server instance holder - allows lazy initialization
 * to avoid circular dependency issues
 */
let _server: SetupServer | null = null

/**
 * Set the server instance (called from server.ts after initialization)
 */
export function setServerInstance(server: SetupServer) {
  _server = server
}

/**
 * Get the server instance
 * Throws if called before server is initialized
 */
export function getServer(): SetupServer {
  if (!_server) {
    throw new Error(
      'MSW server not initialized. Make sure server.ts is imported before using scenarios.'
    )
  }
  return _server
}
