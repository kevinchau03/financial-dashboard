import httpx
import pytest
from app import auth, main


@pytest.fixture
def real_auth(client, monkeypatch):
    main.app.dependency_overrides.pop(auth.get_current_user)
    monkeypatch.setenv('SUPABASE_URL', 'https://auth-test.supabase.co')
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'sb_publishable_test')
    return client


@pytest.mark.parametrize('method,url', [
    ('get', '/api/accounts'), ('post', '/api/accounts'), ('get', '/api/goals'),
    ('post', '/api/goals/1/contributions'), ('delete', '/api/goals/1'),
    ('get', '/api/debts'), ('get', '/api/bills'), ('get', '/api/paycheques'),
    ('post', '/api/paycheques/1/allocations/1/complete'),
    ('get', '/api/payments'), ('delete', '/api/payments/1'),
    ('get', '/api/statements'), ('get', '/api/statements/1/file'),
    ('get', '/api/statements/1/insights'), ('get', '/api/analytics/savings'),
    ('post', '/api/upload_csv'), ('get', '/api/auth/me'),
])
def test_financial_routes_require_auth(real_auth, method, url):
    response = getattr(real_auth, method)(url)
    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'
    assert response.headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('status,body,expected', [
    (401, {}, 401), (403, {}, 401), (500, {}, 503),
    (200, {'id': 'bad'}, 503),
    (200, {'id': '00000000-0000-4000-8000-000000000001', 'role': 'anon'}, 401),
    (200, {'id': '00000000-0000-4000-8000-000000000001', 'role': 'authenticated', 'is_anonymous': True}, 401),
])
def test_invalid_expired_or_anonymous_sessions_fail_closed(real_auth, monkeypatch, status, body, expected):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status, json=body))) as provider:
        monkeypatch.setattr(auth, 'auth_client', lambda: provider)
        assert real_auth.get('/api/accounts', headers={'Authorization': 'Bearer invalid-test-token'}).status_code == expected


def test_provider_outage_is_retryable(real_auth, monkeypatch):
    def offline(request):
        raise httpx.ConnectError('offline', request=request)
    with httpx.Client(transport=httpx.MockTransport(offline)) as provider:
        monkeypatch.setattr(auth, 'auth_client', lambda: provider)
        assert real_auth.get('/api/accounts', headers={'Authorization': 'Bearer test-token'}).status_code == 503


def test_verified_identity_comes_from_provider(real_auth, monkeypatch):
    def verify(request):
        assert str(request.url) == 'https://auth-test.supabase.co/auth/v1/user'
        assert request.headers['apikey'] == 'sb_publishable_test'
        assert request.headers['authorization'] == 'Bearer valid-test-token'
        return httpx.Response(200, json={'id': '00000000-0000-4000-8000-000000000001',
                                       'role': 'authenticated', 'email': 'verified@example.test'})
    with httpx.Client(transport=httpx.MockTransport(verify)) as provider:
        monkeypatch.setattr(auth, 'auth_client', lambda: provider)
        response = real_auth.get('/api/auth/me', headers={'Authorization': 'Bearer valid-test-token'})
        assert response.status_code == 200
        assert response.json()['email'] == 'verified@example.test'


def test_public_settings_never_return_a_secret_key(real_auth, monkeypatch):
    assert real_auth.get('/api/health').status_code == 200
    assert real_auth.get('/api/auth/config').json() == {'url': 'https://auth-test.supabase.co', 'publishable_key': 'sb_publishable_test'}
    monkeypatch.setenv('SUPABASE_PUBLISHABLE_KEY', 'sb_secret_not-a-real-key')
    response = real_auth.get('/api/auth/config')
    assert response.status_code == 503
    assert 'sb_secret' not in response.text
