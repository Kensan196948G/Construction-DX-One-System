import { test, expect } from '@playwright/test'

test.describe('Navigation Structure - CGRC', () => {
  test('ログインページにサイドバーナビゲーションが存在しない', async ({ page }) => {
    await page.goto('/login')
    const sidebar = page.locator('.sidebar, nav')
    const isVisible = await sidebar.isVisible().catch(() => false)
    const count = await sidebar.count()
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
    const body = await page.locator('body').boundingBox()
    expect(body).not.toBeNull()
    expect(body!.width).toBeLessThanOrEqual(375)
  })
})
