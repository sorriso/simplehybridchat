// path: tests/helpers/assertions.ts
// version: 2 - Added jest-dom import for custom matchers

import '@testing-library/jest-dom';

/**
 * Custom assertions for common test scenarios
 */

/**
 * Assert that user has specific permissions
 */
export function expectUserPermissions(
    permissions: any,
    expected: {
      canUseApp?: boolean
      canManageOwnPreferences?: boolean
      canShareOwnConversations?: boolean
      canManageGroupMembers?: boolean
      canManageAllUsers?: boolean
    }
  ) {
    Object.entries(expected).forEach(([key, value]) => {
      expect(permissions[key]).toBe(value)
    })
  }
  
  /**
   * Assert that element has loading state
   */
  export function expectLoadingState(element: HTMLElement) {
    expect(element).toBeInTheDocument()
    expect(
      element.textContent?.toLowerCase().includes('loading') ||
      element.querySelector('[data-loading="true"]') !== null
    ).toBe(true)
  }
  
  /**
   * Assert that error is displayed
   */
  export function expectErrorMessage(container: HTMLElement, message?: string) {
    const errorElement = container.querySelector('[role="alert"]') ||
                          container.querySelector('.error') ||
                          container.querySelector('[data-error="true"]')
    
    expect(errorElement).toBeInTheDocument()
    
    if (message) {
      expect(errorElement?.textContent).toContain(message)
    }
  }
  
  /**
   * Assert that element is disabled
   */
  export function expectDisabled(element: HTMLElement) {
    expect(element).toBeDisabled()
    expect(element).toHaveAttribute('disabled')
  }
  
  /**
   * Assert that element is enabled
   */
  export function expectEnabled(element: HTMLElement) {
    expect(element).not.toBeDisabled()
    expect(element).not.toHaveAttribute('disabled')
  }
  
  /**
   * Assert that modal is open
   */
  export function expectModalOpen(modalTitle: string) {
    const dialog = document.querySelector('[role="dialog"]')
    expect(dialog).toBeInTheDocument()
    expect(dialog?.textContent).toContain(modalTitle)
  }
  
  /**
   * Assert that modal is closed
   */
  export function expectModalClosed() {
    const dialog = document.querySelector('[role="dialog"]')
    expect(dialog).not.toBeInTheDocument()
  }
  
  /**
   * Assert that list has specific number of items
   */
  export function expectListLength(
    container: HTMLElement,
    selector: string,
    length: number
  ) {
    const items = container.querySelectorAll(selector)
    expect(items).toHaveLength(length)
  }
  
  /**
   * Assert that API was called with correct payload
   */
  export function expectApiCalledWith(
    mockFetch: jest.Mock,
    url: string,
    method: string,
    body?: any
  ) {
    const calls = mockFetch.mock.calls
    const matchingCall = calls.find(call => 
      call[0].includes(url) && 
      (!method || call[1]?.method === method)
    )
    
    expect(matchingCall).toBeDefined()
    
    if (body) {
      const callBody = JSON.parse(matchingCall[1]?.body || '{}')
      expect(callBody).toEqual(body)
    }
  }
  
  /**
   * Assert that element has specific role and state
   */
  export function expectRoleAndState(
    element: HTMLElement,
    role: string,
    state?: { [key: string]: string }
  ) {
    expect(element).toHaveAttribute('role', role)
    
    if (state) {
      Object.entries(state).forEach(([attr, value]) => {
        expect(element).toHaveAttribute(`aria-${attr}`, value)
      })
    }
  }
  
  /**
   * Assert conversation is displayed
   */
  export function expectConversationInList(
    container: HTMLElement,
    title: string
  ) {
    const conversations = container.querySelectorAll('[data-testid="conversation-item"]')
    const found = Array.from(conversations).some(
      conv => conv.textContent?.includes(title)
    )
    expect(found).toBe(true)
  }
  
  /**
   * Assert badge is present
   */
  export function expectBadge(
    element: HTMLElement,
    badgeText: string
  ) {
    const badge = element.querySelector('[data-badge]') ||
                  element.querySelector('.badge')
    expect(badge).toBeInTheDocument()
    expect(badge?.textContent).toContain(badgeText)
  }