"""
Send a Tencent Cloud SES template email.

Required env:
  TENCENTCLOUD_SECRET_ID
  TENCENTCLOUD_SECRET_KEY
  TENCENT_SES_REGION=ap-guangzhou
  TENCENT_SES_TEMPLATE_ID
  EMAIL_FROM=Glynk <noreply@example.com>

Install:
  pip install tencentcloud-sdk-python-common tencentcloud-sdk-python-ses python-dotenv

Run:
  python scripts/send_tencent_ses_email_example.py 919756752@qq.com 123456
"""
import json
import os
import sys

from dotenv import load_dotenv
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ses.v20201002 import models, ses_client


def send_template_email(to_email: str, code: str) -> dict:
    load_dotenv()

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

    req = models.SendEmailRequest()
    params = {
        "FromEmailAddress": os.environ["EMAIL_FROM"],
        "Destination": [to_email],
        "Subject": "你的 Glynk 登录验证码",
        "Template": {
            "TemplateID": int(os.environ["TENCENT_SES_TEMPLATE_ID"]),
            "TemplateData": json.dumps({"code": code}, ensure_ascii=False),
        },
        "TriggerType": 1,
    }

    req.from_json_string(json.dumps(params, ensure_ascii=False))
    resp = client.SendEmail(req)
    return json.loads(resp.to_json_string())


if __name__ == "__main__":
    try:
        email = sys.argv[1]
        code = sys.argv[2] if len(sys.argv) > 2 else "123456"
        result = send_template_email(email, code)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except IndexError:
        print("Usage: python scripts/send_tencent_ses_email_example.py <to_email> [code]")
        raise SystemExit(2)
    except TencentCloudSDKException as exc:
        print(f"TencentCloudSDKException: {exc}")
        raise SystemExit(1)
