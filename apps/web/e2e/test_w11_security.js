const { test, expect } = require('@playwright/test');

test.describe('W11 Production Security & CSRF Tests', () => {

  test('CSRF Protection: POST to API proxy without Origin/Referer is rejected', async ({ request }) => {
    // Attempt a direct POST request to a state-changing endpoint via the BFF proxy
    // but without passing an Origin or Referer header that matches the application host.
    const response = await request.post('/api/proxy/v1/personal/history', {
      headers: {
        'Cookie': 'session=fake_cookie_for_test',
        // Purposely omitting Origin and Referer, or setting them to a malicious site
        'Origin': 'https://malicious-site.com',
      },
      data: {
        title_id: 'some_id'
      }
    });

    // The BFF should block this due to CSRF origin mismatch
    expect(response.status()).toBe(403);
    
    const body = await response.json();
    expect(body.error.code).toBe('FORBIDDEN');
    expect(body.error.message).toContain('CSRF');
  });

});
