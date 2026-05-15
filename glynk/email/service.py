"""
Transactional email delivery.

The app currently sends auth-code emails through Tencent Cloud SES templates.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    """Raised when the configured email provider cannot send a message."""


def send_auth_code_email(to_email: str, code: str) -> dict:
    """Send a registration verification code."""
    provider = os.getenv("MAIL_PROVIDER", "tencent_ses").strip().lower()
    if provider in {"console", "log"}:
        logger.warning("Auth code for %s: %s", to_email, code)
        return {"MessageId": "console"}
    if provider != "tencent_ses":
        raise EmailDeliveryError(f"Unsupported MAIL_PROVIDER: {provider}")

    return _send_tencent_ses_template(
        to_email=to_email,
        subject="你的 Glynk 注册验证码",
        template_data={"code": code},
    )


def _send_tencent_ses_template(to_email: str, subject: str,
                               template_data: dict) -> dict:
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.ses.v20201002 import models, ses_client
    except ImportError as exc:
        raise EmailDeliveryError("Tencent Cloud SES SDK is not installed") from exc

    required = [
        "TENCENTCLOUD_SECRET_ID",
        "TENCENTCLOUD_SECRET_KEY",
        "TENCENT_SES_TEMPLATE_ID",
        "EMAIL_FROM",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise EmailDeliveryError(f"Missing email env vars: {', '.join(missing)}")

    cred = credential.Credential(
        os.environ["TENCENTCLOUD_SECRET_ID"],
        os.environ["TENCENTCLOUD_SECRET_KEY"],
    )

    http_profile = HttpProfile()
    http_profile.endpoint = "ses.tencentcloudapi.com"

    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile

    client = ses_client.SesClient(
        cred,
        os.getenv("TENCENT_SES_REGION", "ap-guangzhou"),
        client_profile,
    )

    params = {
        "FromEmailAddress": os.environ["EMAIL_FROM"],
        "Destination": [to_email],
        "Subject": subject,
        "Template": {
            "TemplateID": int(os.environ["TENCENT_SES_TEMPLATE_ID"]),
            "TemplateData": json.dumps(template_data, ensure_ascii=False),
        },
        "TriggerType": 1,
    }

    req = models.SendEmailRequest()
    req.from_json_string(json.dumps(params, ensure_ascii=False))
    resp = client.SendEmail(req)
    result = json.loads(resp.to_json_string())
    logger.info("Sent auth email to %s: %s", to_email, result.get("MessageId"))
    return result
