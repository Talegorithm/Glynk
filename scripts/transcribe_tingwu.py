#!/usr/bin/env python3
"""
使用阿里云 OSS + 听悟 API 转录音频文件。
特点：说话人分离、章节摘要、口语书面化。

依赖：pip install oss2 aliyun-python-sdk-core requests

环境变量（或直接修改下方常量）：
  ALIYUN_AK_ID, ALIYUN_AK_SECRET, TINGWU_APPKEY
"""

import os
import sys
import json
import time
import datetime
import argparse
import requests
import oss2
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

# === 默认配置（可通过环境变量覆盖）===
AK_ID = os.environ.get("ALIYUN_AK_ID", "LTAI5tRnXAi8KX2Bpiy1Szrn")
AK_SECRET = os.environ.get("ALIYUN_AK_SECRET", "DnUI3L3jcH9eeZUpvnjkI7MaiF1cPK")
APPKEY = os.environ.get("TINGWU_APPKEY", "MpdJomw8JTw4Znut")

OSS_ENDPOINT = "https://oss-cn-beijing.aliyuncs.com"
OSS_BUCKET_NAME = "tingwu-temp-transcribe"
OSS_REGION = "cn-beijing"

TINGWU_DOMAIN = "tingwu.cn-beijing.aliyuncs.com"
TINGWU_VERSION = "2023-09-30"


def ensure_oss_bucket(auth, endpoint, bucket_name):
    bucket = oss2.Bucket(auth, endpoint, bucket_name)
    try:
        bucket.get_bucket_info()
    except oss2.exceptions.NoSuchBucket:
        bucket.create_bucket()
        rule = oss2.models.LifecycleRule(
            "auto-cleanup", "", status=oss2.models.LifecycleRule.ENABLED,
            expiration=oss2.models.LifecycleExpiration(days=1)
        )
        bucket.put_bucket_lifecycle(oss2.models.BucketLifecycle([rule]))
    return bucket


def upload_to_oss(bucket, local_path):
    filename = os.path.basename(local_path)
    oss_key = f"voice-memos/{filename}"
    bucket.put_object_from_file(oss_key, local_path)
    return bucket.sign_url('GET', oss_key, 6 * 3600)


def create_tingwu_task(client, file_url, task_name, speaker_count=0):
    body = {
        "AppKey": APPKEY,
        "Input": {
            "SourceLanguage": "cn",
            "TaskKey": task_name,
            "FileUrl": file_url,
        },
        "Parameters": {
            "Transcription": {
                "DiarizationEnabled": True,
                "Diarization": {"SpeakerCount": speaker_count},
            },
            "AutoChaptersEnabled": True,
            "SummarizationEnabled": True,
            "Summarization": {"Types": ["Paragraph", "Conversational"]},
            "TextPolishEnabled": True,
        },
    }

    request = CommonRequest()
    request.set_accept_format("json")
    request.set_domain(TINGWU_DOMAIN)
    request.set_version(TINGWU_VERSION)
    request.set_protocol_type("https")
    request.set_method("PUT")
    request.set_uri_pattern("/openapi/tingwu/v2/tasks")
    request.add_header("Content-Type", "application/json")
    request.add_query_param("type", "offline")
    request.set_content(json.dumps(body).encode("utf-8"))

    response = client.do_action_with_exception(request)
    result = json.loads(response)
    if result.get("Code") == "0":
        return result["Data"]["TaskId"]
    else:
        raise RuntimeError(f"任务创建失败: {result}")


def poll_task(client, task_id, max_wait=600, interval=15):
    request = CommonRequest()
    request.set_accept_format("json")
    request.set_domain(TINGWU_DOMAIN)
    request.set_version(TINGWU_VERSION)
    request.set_protocol_type("https")
    request.set_method("GET")
    request.set_uri_pattern(f"/openapi/tingwu/v2/tasks/{task_id}")

    elapsed = 0
    while elapsed < max_wait:
        response = client.do_action_with_exception(request)
        result = json.loads(response)
        status = result.get("Data", {}).get("TaskStatus")
        print(f"  [{elapsed}s] {status}")
        if status == "COMPLETED":
            return result["Data"]
        elif status == "FAILED":
            raise RuntimeError(f"任务失败: {result}")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError("任务超时")


def download_results(result_data):
    output = {}
    result = result_data.get("Result", {})

    if "Transcription" in result:
        resp = requests.get(result["Transcription"])
        transcription = resp.json()
        output["transcription"] = transcription
        paragraphs = transcription.get("Transcription", {}).get("Paragraphs", [])
        full_text, current_speaker = [], None
        for para in paragraphs:
            words = para.get("Words", [])
            speaker = para.get("SpeakerId", "")
            text = "".join(w.get("Text", "") for w in words)
            if text.strip():
                if speaker != current_speaker:
                    current_speaker = speaker
                    full_text.append(f"\n【说话人 {speaker}】")
                full_text.append(text)
        output["text"] = "\n".join(full_text)

    for key in ["AutoChapters", "Summarization", "TextPolish"]:
        if key in result:
            resp = requests.get(result[key])
            output[key.lower()] = resp.json()

    return output


def main():
    parser = argparse.ArgumentParser(description="听悟语音转录")
    parser.add_argument("files", nargs="+", help="音频文件路径")
    parser.add_argument("-o", "--output-dir", default=".", help="输出目录")
    parser.add_argument("--speakers", type=int, default=0, help="说话人数（0=自动检测）")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    auth = oss2.Auth(AK_ID, AK_SECRET)
    credentials = AccessKeyCredential(AK_ID, AK_SECRET)
    client = AcsClient(region_id=OSS_REGION, credential=credentials)
    bucket = ensure_oss_bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

    for audio_file in args.files:
        name = os.path.splitext(os.path.basename(audio_file))[0]
        print(f"\n{'='*50}\n处理: {name}\n{'='*50}")

        url = upload_to_oss(bucket, audio_file)
        print("OSS 上传完成")

        task_key = f"vm-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        task_id = create_tingwu_task(client, url, task_key, args.speakers)
        print(f"任务已创建: {task_id}")

        task_data = poll_task(client, task_id)
        parsed = download_results(task_data)

        json_path = os.path.join(args.output_dir, f"{name}_tingwu.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)

        txt_path = os.path.join(args.output_dir, f"{name}_tingwu.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(parsed.get("text", ""))

        print(f"结果已保存: {json_path}, {txt_path}")


if __name__ == "__main__":
    main()
