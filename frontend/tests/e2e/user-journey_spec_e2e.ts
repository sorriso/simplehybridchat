// path: tests/e2e/user-journey_spec.e2e.ts
// version: 1

import { test, expect } from '@playwright/test'

test.describe('User Journey E2E', () => {
  test('loads the application homepage', async ({ page }) => {
    await page.goto('/')
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle')
    
    // Check that we're on the right page
    await expect(page).toHaveURL('/')
    
    // Basic check that the page loaded
    await expect(page.locator('body')).toBeVisible()
  })

  test('can navigate to login page', async ({ page }) => {
    await page.goto('/')
    
    // Look for a login button or link
    const loginButton = page.getByRole('button', { name: /log in|login|sign in/i })
    
    if (await loginButton.isVisible()) {
      await loginButton.click()
      
      // Should see a login form
      await expect(page.getByLabel(/email|username/i)).toBeVisible()
      await expect(page.getByLabel(/password/i)).toBeVisible()
    }
  })
})