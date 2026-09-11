import json
import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.routers.auth import verify_google_id_token


@pytest.mark.parametrize('change', ['valid', 'expired', 'issuer', 'audience', 'missing_audience', 'signature'])
def test_google_library_verifies_signed_claims(monkeypatch, change):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    now = int(time.time())
    claims = dict(iss='https://accounts.google.com', aud='test-client-id', sub='synthetic-sub',
                  iat=now - 10, exp=now + 300, email='synthetic@gmail.com', email_verified=True)
    if change == 'expired': claims['exp'] = now - 1
    if change == 'issuer': claims['iss'] = 'https://other.example.test'
    if change == 'audience': claims['aud'] = 'other-client'
    if change == 'missing_audience': del claims['aud']
    signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048) if change == 'signature' else key
    token = jwt.encode(claims, signing_key, algorithm='RS256', headers={'kid': 'synthetic-key'})
    def certificates(self, url, **kwargs):
        assert kwargs['timeout'] == 5
        assert 'token' not in url
        return SimpleNamespace(status=200, data=json.dumps({'synthetic-key': public}).encode())
    monkeypatch.setattr('backend.routers.auth.GoogleRequest.__call__', certificates)
    if change == 'valid':
        assert verify_google_id_token(token)['sub'] == 'synthetic-sub'
    else:
        with pytest.raises(Exception):
            verify_google_id_token(token)
