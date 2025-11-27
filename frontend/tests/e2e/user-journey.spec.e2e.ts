// path: tests/e2e/user-journey.spec.e2e.ts
// version: 1

import { test, expect } from '@playwright/test'

test.describe('Complete User Journey', () => {
  test('full workflow: login → chat → upload → settings → logout', async ({ page }) => {
    // Login
    await page.goto('http://localhost:3000')
    await page.fill('[name="email"]', 'john.doe@example.com')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    
    await expect(page).toHaveURL(/.*chat/)
    
    // Create conversation
    await page.click('button:has-text("New Chat")')
    await expect(page.locator('.conversation-item')).toHaveCount(1)
    
    // Send message
    await page.fill('[placeholder="Type a message"]', 'Hello Claude!')
    await page.press('[placeholder="Type a message"]', 'Enter')
    
    // Wait for streaming response
    await expect(page.locator('.message-assistant')).toBeVisible({ timeout: 10000 })
    
    // Upload file
    await page.click('button[aria-label="Upload file"]')
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('PDF content'),
    })
    await page.click('button:has-text("Upload")')
    await expect(page.locator('.file-item')).toContainText('test.pdf')
    
    // Update settings
    await page.click('button[aria-label="Settings"]')
    await page.fill('[name="promptCustomization"]', 'Be very concise')
    await page.click('button:has-text("Save")')
    await expect(page.locator('.toast-success')).toBeVisible()
    
    // Force logout
    await page.click('button:has-text("Force Logout")')
    await page.waitForURL('/')
    
    // Verify logged out
    await expect(page.locator('form')).toContainText('Login')
  })

  test('handles errors gracefully', async ({ page }) => {
    // Simulate network error
    await page.route('**/api/chat/stream', route => route.abort())
    
    await page.goto('http://localhost:3000/chat')
    
    await page.fill('[placeholder="Type a message"]', 'Test message')
    await page.press('[placeholder="Type a message"]', 'Enter')
    
    // Should show error message
    await expect(page.locator('.error-message')).toBeVisible()
  })

  test('maintains state across navigation', async ({ page }) => {
    await page.goto('http://localhost:3000/chat')
    
    // Create conversation
    await page.click('button:has-text("New Chat")')
    await page.fill('[placeholder="Type a message"]', 'Test')
    await page.press('[placeholder="Type a message"]', 'Enter')
    
    // Navigate to settings
    await page.click('button[aria-label="Settings"]')
    await expect(page.locator('.settings-panel')).toBeVisible()
    
    // Navigate back
    await page.click('button[aria-label="Back to chat"]')
    
    // Conversation should still be there
    await expect(page.locator('.conversation-item')).toHaveCount(1)
  })
})
