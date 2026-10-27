# ContentIQ External Platform Integrations & Signed Webhooks Setup Guide

## Overview

ContentIQ provides an adapter-based integration layer designed to ingest submissions, sync rubrics, and deliver evaluation results with enterprise external systems strictly through official APIs and authorized access:

- **Google Forms API v1** — Automated quiz and essay form submission ingestion.
- **Typeform Responses API** — Candidate application and assessment ingestion.
- **Canvas LMS REST API v1** — Assignment submission sync and grade writeback.
- **Moodle Web Services Protocol** — Assessment submission ingestion and rubric evaluation.
- **Blackboard Learn REST API** — Course attempt synchronization.
- **Custom Client Applications** — Generic HTTP / API key / HMAC integration.
- **Mock Adapter** — Deterministic offline testing and CI/CD verification.
- **Signed Webhooks Engine** — Real-time event notifications with HMAC-SHA256 signatures, replay defense, and delivery audit logging.

---

## Security Architecture & Guarantees

1. **Encrypted Secret Storage at Rest**:
   - All sensitive secrets (API keys, OAuth tokens, personal access tokens) are stored in the database **only as Fernet-encrypted bytes** (AES-128-CBC with PKCS7 padding and HMAC authentication).
   - Encryption keys are derived from `SECRET_KEY` or `INTEGRATION_ENCRYPTION_KEY`.
2. **Zero Secret Leakage**:
   - The API **NEVER returns secrets** in any GET or response payload. Responses expose a safe `has_secrets: bool` flag.
3. **Official APIs Only**:
   - Private pages are never scraped. No undocumented or invented endpoints are used.
4. **Data Minimization & Privacy Protection**:
   - Default webhook delivery payloads include **only summary metrics and status metadata**. Full student essays and raw media binaries are suppressed unless `include_full_payload` is explicitly authorized.
5. **Role-Based Access Control (RBAC)**:
   - Creating, modifying, testing, disconnecting, or deleting integrations and webhooks requires the `admin` or `reviewer` role. Ordinary users cannot access secret management.

---

## Platform Setup Instructions

### 1. Google Forms API v1

Official Documentation: [Google Forms API Guides](https://developers.google.com/forms/api/guides)

#### Required API Permissions / Scopes
- `https://www.googleapis.com/auth/forms.responses.readonly` — Read form responses and timestamps.
- `https://www.googleapis.com/auth/forms.body.readonly` — Read form structure, questions, and metadata.

#### Setup Steps
1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project and enable the **Google Forms API** from the API Library.
3. Configure the **OAuth Consent Screen** (User Type: Internal or External).
4. Go to **Credentials** → **Create Credentials** → **OAuth Client ID** (Application type: Web application).
5. Obtain the `access_token` via OAuth 2.0 flow or service account.
6. Register the integration in ContentIQ:
   ```bash
   POST /api/v1/integrations
   {
     "provider": "google_forms",
     "display_name": "University Admissions Form",
     "auth_method": "oauth2",
     "config": {
       "form_id": "1FAIpQLSc..."
     },
     "secrets": {
       "access_token": "ya29.a0AfH6S..."
     }
   }
   ```

---

### 2. Typeform Responses API

Official Documentation: [Typeform Developer Portal](https://www.typeform.com/developers/responses/reference/retrieve-responses/)

#### Required API Permissions / Scopes
- `responses:read` — Access respondent submissions.
- `forms:read` — Read form questions and block definitions.

#### Setup Steps
1. Log in to [Typeform](https://admin.typeform.com/) and navigate to **Account** → **Developer Apps**.
2. Click **Generate Personal Access Token** or create an OAuth app.
3. Copy the token (prefix: `tfp_...`).
4. In ContentIQ:
   ```bash
   POST /api/v1/integrations
   {
     "provider": "typeform",
     "display_name": "Applicant Essay Questionnaire",
     "auth_method": "pat",
     "config": {
       "form_id": "u6n21b"
     },
     "secrets": {
       "access_token": "tfp_..."
     }
   }
   ```

---

### 3. Instructure Canvas LMS REST API

Official Documentation: [Canvas LMS API](https://canvas.instructure.com/doc/api/all_resources.html)

#### Required Endpoints & Scopes
- `url:GET|/api/v1/users/self` — Identity verification.
- `url:GET|/api/v1/courses/:course_id/assignments` — Assignment listing.
- `url:GET|/api/v1/courses/:course_id/assignments/:assignment_id/submissions` — Submission download.

#### Setup Steps
1. In your institution's Canvas instance (`https://yourinstitution.instructure.com`), navigate to **Account** → **Settings**.
2. Scroll to **Approved Integrations** and click **+ New Access Token**.
3. Set Purpose to "ContentIQ Platform" and copy the token.
4. In ContentIQ:
   ```bash
   POST /api/v1/integrations
   {
     "provider": "canvas_lms",
     "display_name": "Spring 2026 CS101 Canvas",
     "auth_method": "bearer_token",
     "config": {
       "base_url": "https://yourinstitution.instructure.com",
       "course_id": "12345"
     },
     "secrets": {
       "access_token": "7~abcdef..."
     }
   }
   ```

---

### 4. Moodle Web Services Protocol

Official Documentation: [Moodle Web Services](https://docs.moodle.org/dev/Web_service_API_functions)

#### Required Capabilities
- `core_webservice_get_site_info` — Site verification.
- `mod/assign:viewgrades` — Assignment access.
- `moodle/course:view` — Course access.

#### Setup Steps
1. In Moodle as Administrator:
   - Go to **Site Administration** → **Server** → **Web Services**.
   - Enable **REST protocol**.
   - Create a service user and assign appropriate role capabilities.
   - Generate a Web Service token for the user.
2. In ContentIQ:
   ```bash
   POST /api/v1/integrations
   {
     "provider": "moodle",
     "display_name": "Moodle Faculty Portal",
     "auth_method": "token",
     "config": {
       "base_url": "https://moodle.university.edu",
       "course_id": "42"
     },
     "secrets": {
       "wstoken": "9f8e7d6c5b4a..."
     }
   }
   ```

---

### 5. Blackboard Learn REST API

Official Documentation: [Blackboard Developer Portal](https://developer.blackboard.com/portal/displayApi)

#### Required Entitlements
- `course.content.VIEW`
- `course.gradebook.MODIFY`
- `system.administration.VIEW`

#### Setup Steps
1. Register your application in the [Anthology Developer Portal](https://developer.blackboard.com/).
2. Note your **Application ID**, **Client ID**, and **Client Secret**.
3. In Blackboard System Admin → **REST API Integrations**, register the Application ID.
4. In ContentIQ:
   ```bash
   POST /api/v1/integrations
   {
     "provider": "blackboard",
     "display_name": "Anthology Learn Production",
     "auth_method": "client_credentials",
     "config": {
       "base_url": "https://blackboard.institution.edu"
     },
     "secrets": {
       "client_id": "...",
       "client_secret": "..."
     }
   }
   ```

---

## Signed Webhooks Implementation Guide

### Outgoing Headers
Every webhook event dispatched by ContentIQ carries standard HTTP headers:

| Header | Description | Example |
|---|---|---|
| `X-ContentIQ-Event-ID` | Unique UUID (same across retries for idempotency) | `3c8d102e-5f91-4d7a-8b1e-2c9b4e7a8f10` |
| `X-ContentIQ-Event` | Event type identifier | `job.completed`, `batch.completed` |
| `X-ContentIQ-Timestamp` | Unix timestamp (seconds) when signature was computed | `1793041200` |
| `X-ContentIQ-Signature-256` | HMAC-SHA256 hex signature | `sha256=a1b2c3d4...` |

### Webhook Verification Code Examples

#### Python Verification Example
```python
import hashlib
import hmac
import time

def verify_contentiq_webhook(
    secret: str,
    raw_body: bytes,
    signature_header: str,
    timestamp_header: str,
    tolerance_seconds: int = 300,
) -> bool:
    # 1. Replay defense: verify timestamp freshness
    current_time = int(time.time())
    event_time = int(timestamp_header)
    if abs(current_time - event_time) > tolerance_seconds:
        return False  # Replay attack or excessive clock drift

    # 2. Compute expected HMAC-SHA256 signature
    computed_mac = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256)
    expected_header = f"sha256={computed_mac.hexdigest()}"

    # 3. Constant-time comparison prevents timing attacks
    return hmac.compare_digest(expected_header, signature_header)
```

#### Node.js / TypeScript Verification Example
```typescript
import * as crypto from "crypto";

export function verifyWebhook(
  secret: string,
  rawBody: Buffer,
  signatureHeader: string,
  timestampHeader: string,
  toleranceSeconds: number = 300
): boolean {
  const currentTime = Math.floor(Date.now() / 1000);
  const eventTime = parseInt(timestampHeader, 10);

  if (Math.abs(currentTime - eventTime) > toleranceSeconds) {
    return false; // Replay attack detected
  }

  const expectedSignature =
    "sha256=" +
    crypto
      .createHmac("sha256", secret)
      .update(rawBody)
      .digest("hex");

  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(signatureHeader)
  );
}
```

---

## Retry Policy & Idempotency

- Retries use exponential backoff: 30s, 120s, 480s, 1920s, 7200s (up to 5 attempts).
- Each retry attempt retains the identical `X-ContentIQ-Event-ID`. Receivers should cache processed `event_id`s to ensure idempotent processing.
- Failed deliveries are logged in the `webhook_deliveries` audit table with HTTP response status, error message, and truncated target response body.
