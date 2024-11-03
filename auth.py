import os
from jose import JWTError, jwt
from fastapi import HTTPException, Request
from dotenv import load_dotenv
import requests


# Load environment variables
load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_SECRET = os.getenv("AUTH0_SECRET")
ALGORITHMS = [os.getenv("AUTH0_ALGORITHM")]
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

def get_auth0_token():
    url = f'https://{AUTH0_DOMAIN}/oauth/token'
    headers = { 'content-type': 'application/json' }
    payload = {
        'client_id': AUTH0_CLIENT_ID,
        'client_secret': AUTH0_CLIENT_SECRET,
        'audience': f'https://{AUTH0_DOMAIN}/api/v2/',
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()['access_token']

# Function to get the JWKS from Auth0
def get_jwks():
    jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
    jwks = requests.get(jwks_url).json()
    return jwks['keys']

# Function to find the RSA key from the JWKS based on the 'kid' in the token header
def get_rsa_key(token: str):
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Unable to find appropriate key")
        return rsa_key
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"JWT decoding error: {str(e)}")

# Function to verify and decode the JWT using the RSA key
def verify_jwt(token: str):
    rsa_key = get_rsa_key(token)
    try:
        payload = jwt.decode(
            token,
            rsa_key,  # Use the RSA key retrieved from JWKS
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

# Function to extract and verify the user from the request
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Authorization header missing")
    
    token = auth_header.split(" ")[1]
    return verify_jwt(token)  # Decode and verify the token
