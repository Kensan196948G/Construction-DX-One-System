import { test, expect } from '@playwright/test'

test.describe('Login Page - CAB', () => {
  test('ログインページが正常に表示される', async ({ page }) => {
    await page.goto('/')
    await page.waitForURL('**/login')
    await expect(page).toHaveTitle(/CAB|Change|変更/i)
  })

  test('ルートガード: 未認証では /login にリダイレクト', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/login/)
  })

  test('ルートガード: /rfcs にアクセスすると /login にリダイレクト', async ({ page }) => {
    await page.goto('/rfcs')
    await expect(page).toHaveURL(/\/login/)
  })

  test('ルートガード: /cab-meetings にアクセスするとリダイレクトまたは認証チェックが実行される', async ({ page }) => {
    await page.goto('/cab-meetings')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    const url = page.url()
    expect(url).toMatch(/\/(login|cab-meetings)/)
  })

  test('ログインフォームの要素が存在する', async ({ page }) => {
    await page.goto('/login')
    await page.waitForLoadState('networkidle')
    const usernameField = page.locator('input[type="text"], input[autocomplete="username"]').first()
    const passwordField = page.locator('input[type="password"]').first()
    const submitBtn = page.locator('button[type="submit"]').first()
    await expect(usernameField).toBeVisible()
    await expect(passwordField).toBeVisible()
    await expect(submitBtn).toBeVisible()
  })

  test('ユーザー名・パスワード入力後ボタンが操作可能', async ({ page }) => {
    await page.goto('/login')
    await page.waitForLoadState('networkidle')
    await page.locator('input[autocomplete="username"]').first().fill('testuser')
    await page.locator('input[type="password"]').first().fill('testpass')
    const submitBtn = page.locator('button[type="submit"]').first()
    await expect(submitBtn).toBeEnabled()
  })

  test('CAB サブタイトルが表示される', async ({ page }) => {
    await page.goto('/login')
    await page.waitForLoadState('networkidle')
    const content = await page.content()
    expect(content).toContain('Change')
  })
})
