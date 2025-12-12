// path: frontend/jest.setup.js
// version: 7

// Add fetch polyfill FIRST (required for MSW and API calls in tests)
// Node.js doesn't have fetch natively, so we need to polyfill it
if (typeof global.fetch === 'undefined') {
  const nodeFetch = require('node-fetch');
  global.fetch = nodeFetch;
  global.Headers = nodeFetch.Headers;
  global.Request = nodeFetch.Request;
  global.Response = nodeFetch.Response;
}

// Use require instead of import for CommonJS compatibility
require('@testing-library/jest-dom');

// Try to load MSW server if handlers exist, otherwise skip
try {
  const { server } = require('./tests/mocks/server');
  
  // Establish API mocking before all tests
  beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
  
  // Reset handlers after each test
  afterEach(() => server.resetHandlers());
  
  // Clean up after all tests
  afterAll(() => server.close());
} catch (error) {
  // MSW server not available, tests will run without API mocking
  console.log('Ã¢Å¡Â Ã¯Â¸Â  MSW server not loaded (handlers may be missing)');
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn(),
};