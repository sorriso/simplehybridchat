// path: tests/e2e/admin-features.spec.e2e.ts
// version: 1

import { test, expect } from '@playwright/test'

test.describe('Admin Features', () => {
  test.beforeEach(async ({ page }) => {
    // Login as root
    await page.goto('http://localhost:3000')
    await page.fill('[name="email"]', 'admin@example.com')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.waitForURL(/.*chat/)
  })

  test('manager: manage users in groups', async ({ page }) => {
    // Switch to manager account
    await page.click('button[aria-label="Logout"]')
    await page.fill('[name="email"]', 'jane.manager@example.com')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    
    await page.click('button:has-text("Admin")')
    await page.click('text=User Management')
    
    // Should see only managed groups
    await expect(page.locator('.group-filter')).toContainText('Engineering Team')
    await expect(page.locator('.group-filter')).not.toContainText('All Users')
  })

  test('manager: share conversation with group', async ({ page }) => {
    // Switch to manager
    await page.click('button[aria-label="Logout"]')
    await page.fill('[name="email"]', 'jane.manager@example.com')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    
    // Create conversation
    await page.click('button:has-text("New Chat")')
    
    // Right-click to share
    await page.locator('.conversation-item').first().click({ button: 'right' })
    await page.click('text=Share')
    
    // Select group
    await page.check('input[type="checkbox"][value="ugroup-1"]')
    await page.click('button:has-text("Save")')
    
    // Should show shared badge
    await expect(page.locator('.shared-badge')).toBeVisible()
  })

  test('root: create user group', async ({ page }) => {
    await page.click('button:has-text("Admin")')
    await page.click('text=Group Management')
    
    await page.click('button:has-text("Create Group")')
    await page.fill('[name="groupName"]', 'New Team')
    await page.click('button:has-text("Submit")')
    
    await expect(page.locator('.group-list')).toContainText('New Team')
  })

  test('root: assign manager to group', async ({ page }) => {
    await page.click('button:has-text("Admin")')
    await page.click('text=Group Management')
    
    await page.click('.group-item:has-text("Engineering Team") button:has-text("Managers")')
    await page.click('button:has-text("Add Manager")')
    await page.selectOption('select[name="userId"]', 'user-manager')
    await page.click('button:has-text("Confirm")')
    
    await expect(page.locator('.manager-list')).toContainText('Jane Manager')
  })

  test('root: toggle maintenance mode', async ({ page }) => {
    await page.click('button:has-text("Admin")')
    await page.click('text=System Settings')
    
    await page.check('input[name="maintenanceMode"]')
    await page.click('button:has-text("Save")')
    
    await expect(page.locator('.maintenance-banner')).toBeVisible()
  })

  test('root: revoke all sessions', async ({ page }) => {
    await page.click('button:has-text("Admin")')
    await page.click('text=System Settings')
    
    await page.click('button:has-text("Revoke All Sessions")')
    await page.click('button:has-text("Confirm")')
    
    // Should be logged out
    await page.waitForURL('/')
    await expect(page.locator('form')).toContainText('Login')
  })
})
