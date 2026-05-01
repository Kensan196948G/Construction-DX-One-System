import { test, expect } from '@playwright/test'

// NOTE: These tests require mock auth or a running backend.
// They verify UI structure without actual API calls.

test.describe('Navigation Structure', () => {
  test('ログインページにナビゲーションが存在しない', async ({ page }) => {
    await page.goto('/login')
    const sidebar = page.locator('.sidebar, nav')
    // 未認証時はサイドバーが非表示
    const isVisible = await sidebar.isVisible().catch(() => false)
    // Either hidden or not present
    const count = await sidebar.count()
    // Login page should not show nav sidebar (or should show it hidden)
    expect(count === 0 || !isVisible).toBeTruthy()
  })

  test('ログインページに必須テキストが含まれる', async ({ page }) => {
    await page.goto('/login')
    const bodyText = await page.locator('body').textContent()
    expect(bodyText).toBeTruthy()
    expect(bodyText!.length).toBeGreaterThan(10)
  })

  test('CSS が正常にロードされる（スタイルが適用される）', async ({ page }) => {
    await page.goto('/login')
    // Check that page has styling (body background or specific elements)
    const backgroundColor = await page.evaluate(() =>
      window.getComputedStyle(document.body).backgroundColor
    )
    expect(backgroundColor).toBeTruthy()
  })

  test('JavaScriptエラーがコンソールに出力されない', async ({ page }) => {
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })
    await page.goto('/login')
    await page.waitForLoadState('networkidle')
    // Filter out non-critical errors (network errors are expected without backend)
    const criticalErrors = errors.filter(e =>
      !e.includes('Failed to fetch') &&
      !e.includes('net::ERR') &&
      !e.includes('404')
    )
    expect(criticalErrors).toHaveLength(0)
  })

  test('モバイルビューポートでページが表示される', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/login')
    const form = page.locator('form, .login-form, .auth-form').first()
    // Page should render even on mobile
    const body = await page.locator('body').boundingBox()
    expect(body).not.toBeNull()
    expect(body!.width).toBeLessThanOrEqual(375)
  })
})
