// path: tests/e2e/drag-drop.spec.e2e.ts
// version: 1

import { test, expect } from '@playwright/test'

test.describe('Drag and Drop', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/chat')
  })

  test('drag conversation to group', async ({ page }) => {
    // Create a conversation
    await page.click('button:has-text("New Chat")')
    await page.waitForSelector('.conversation-item')
    
    const conversation = page.locator('.conversation-item').first()
    const group = page.locator('.conversation-group').first()
    
    // Drag conversation to group
    await conversation.dragTo(group)
    
    // Verify conversation is now in group
    await expect(group.locator('.conversation-item')).toHaveCount(1)
  })

  test('drop conversation in group', async ({ page }) => {
    await page.click('button:has-text("New Chat")')
    await page.waitForSelector('.conversation-item')
    
    const conversation = page.locator('.conversation-item').first()
    const targetGroup = page.locator('[data-group-id="group-1"]')
    
    // Perform drag and drop
    const conversationBox = await conversation.boundingBox()
    const groupBox = await targetGroup.boundingBox()
    
    if (conversationBox && groupBox) {
      await page.mouse.move(
        conversationBox.x + conversationBox.width / 2,
        conversationBox.y + conversationBox.height / 2
      )
      await page.mouse.down()
      await page.mouse.move(
        groupBox.x + groupBox.width / 2,
        groupBox.y + groupBox.height / 2,
        { steps: 10 }
      )
      await page.mouse.up()
    }
    
    // Verify API call was made
    await page.waitForResponse(resp => 
      resp.url().includes('/api/conversations/') && 
      resp.request().method() === 'PUT'
    )
    
    // Verify group now contains conversation
    await expect(targetGroup.locator('.conversation-item')).toHaveCount(1)
  })

  test('visual feedback during drag', async ({ page }) => {
    await page.click('button:has-text("New Chat")')
    await page.waitForSelector('.conversation-item')
    
    const conversation = page.locator('.conversation-item').first()
    
    // Start dragging
    await conversation.hover()
    await page.mouse.down()
    
    // Should show dragging state
    await expect(conversation).toHaveClass(/dragging/)
    
    // Should show drop zones
    await expect(page.locator('.drop-zone')).toBeVisible()
    
    await page.mouse.up()
  })

  test('cancel drag with ESC key', async ({ page }) => {
    await page.click('button:has-text("New Chat")')
    await page.waitForSelector('.conversation-item')
    
    const conversation = page.locator('.conversation-item').first()
    const originalParent = await conversation.locator('..').getAttribute('data-group-id')
    
    // Start dragging
    await conversation.hover()
    await page.mouse.down()
    
    // Press ESC to cancel
    await page.keyboard.press('Escape')
    
    // Verify conversation didn't move
    const currentParent = await conversation.locator('..').getAttribute('data-group-id')
    expect(currentParent).toBe(originalParent)
  })

  test('drag multiple conversations (future)', async ({ page }) => {
    // This test will fail until multi-select is implemented
    await page.click('button:has-text("New Chat")')
    await page.click('button:has-text("New Chat")')
    await page.waitForSelector('.conversation-item')
    
    // Select multiple conversations (Ctrl+Click)
    const conversations = page.locator('.conversation-item')
    await conversations.nth(0).click({ modifiers: ['Control'] })
    await conversations.nth(1).click({ modifiers: ['Control'] })
    
    // Both should be selected
    await expect(conversations.nth(0)).toHaveClass(/selected/)
    await expect(conversations.nth(1)).toHaveClass(/selected/)
    
    // Drag selected conversations
    const group = page.locator('.conversation-group').first()
    await conversations.nth(0).dragTo(group)
    
    // All selected conversations should move
    await expect(group.locator('.conversation-item')).toHaveCount(2)
  })
})
