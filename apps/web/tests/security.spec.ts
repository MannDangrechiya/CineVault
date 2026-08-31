import { test, expect } from '@playwright/test';

test.describe('W11 Web Security & CSRF Gateway Tests', () => {
  test('BFF Proxy rejects state-changing requests with mismatched Origin (CSRF Attack)', async ({ request }) => {
    const response = await request.post('/api/proxy/v1/personal/library', {
      headers: {
        'Origin': 'https://evil-attacker.com',
        'Content-Type': 'application/json',
      },
      data: { title_id: '018f2e4a-7b31-7000-8000-123456789abf' }
    });
    // Must be rejected with 403 Forbidden
    expect(response.status()).toBe(403);
    const body = await response.json();
    // BFF error envelope is { error: { code, message } }, not a bare string.
    expect(body.error.message).toContain('CSRF verification failed');
  });

  test('BFF Proxy rejects state-changing requests without Origin or Referer', async ({ request }) => {
    const response = await request.post('/api/proxy/v1/personal/library', {
      headers: {
        'Content-Type': 'application/json',
      },
      data: { title_id: '018f2e4a-7b31-7000-8000-123456789abf' }
    });
    // Missing Origin & Referer on state-changing requests must be rejected
    expect(response.status()).toBe(403);
  });

  test('BFF Proxy permits GET read requests without CSRF blocking', async ({ request }) => {
    const response = await request.get('/api/proxy/health/liveness');
    // GET requests should not be blocked by CSRF origin verification
    expect([200, 401, 404, 502, 503]).toContain(response.status());
    expect(response.status()).not.toBe(403);
  });
});
