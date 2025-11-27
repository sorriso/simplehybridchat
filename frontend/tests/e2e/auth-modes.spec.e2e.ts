// path: tests/e2e/auth-modes.spec.e2e.ts
// version: 1

import { test, expect } from '@playwright/test'

test.describe('Authentication Modes', () => {
  test('no-auth mode: auto login', async ({ page }) => {
    await page.route('**/api/auth/config', route =>
      route.fulfill({
        json: { config: { mode: 'none', allowMultiLogin: false, maintenanceMode: false } },
      })
    )
    
    await page.goto('http://localhost:3000')
    
    // Should auto-login and redirect to chat
    await expect(page).toHaveURL(/.*chat/)
    await expect(page.locator('.user-info')).toContainText('John Doe')
  })

  test('local mode: login form', async ({ page }) => {
    await page.route('**/api/auth/config', route =>
      route.fulfill({
        json: { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: false } },
      })
    )
    
    await page.goto('http://localhost:3000')
    
    // Should show login form
    await expect(page.locator('form')).toContainText('Login')
    await expect(page.locator('[name="email"]')).toBeVisible()
    await expect(page.locator('[name="password"]')).toBeVisible()
  })

  test('sso mode: auto login from headers', async ({ page }) => {
    await page.route('**/api/auth/config', route =>
      route.fulfill({
        json: { config: { mode: 'sso', allowMultiLogin: false, maintenanceMode: false } },
      })
    )
    
    await page.route('**/api/auth/sso/verify', route =>
      route.fulfill({
        json: {
          user: {
            id: 'sso-user-1',
            name: 'SSO User',
            email: 'sso@example.com',
            role: 'user',
            status: 'active',
          },
        },
      })
    )
    
    await page.goto('http://localhost:3000')
    
    // Should auto-login from SSO
    await expect(page).toHaveURL(/.*chat/)
    await expect(page.locator('.user-info')).toContainText('SSO User')
  })

  test('maintenance mode: non-root blocked', async ({ page }) => {
    await page.route('**/api/auth/config', route =>
      route.fulfill({
        json: { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: true } },
      })
    )
    
    await page.goto('http://localhost:3000')
    
    await page.fill('[name="email"]', 'john.doe@example.com')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    
    // Should show maintenance message
    await expect(page.locator('.maintenance-banner')).toBeVisible()
    await expect(page.locator('.maintenance-banner')).toContainText('under maintenance')
  })

  test('maintenance mode: root access with banner', async ({ page }) => {
    await page.route('**/api/auth/config', route =>
      route.fulfill({
        json: { config: { mode: 'local', allowMultiLogin: false, maintenanceMode: true } },
      })
    )
    
    await page.goto('http://localhost:3000')
    
    await page.fill('[name="email"]', 'admin@example.com')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    
    // Root can access but sees banner
    await expect(page).toHaveURL(/.*chat/)
    await expect(page.locator('.maintenance-banner')).toBeVisible()
  })
})
