#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_via_api.py —— 走 GitHub API 推送(github.com:443 被阻断时的替代 git push)

前提: 本机 git 凭据管理器中存有 GitHub PAT(repo 权限), 即 `git push` 平时可用。

行为:
  1. 读取本地 git 暂存区(git ls-files)的全部文件;
  2. 在远端 main 最新提交之上, 以本地 HEAD 的提交信息创建一个快照提交;
  3. 将远端 main 移动到该提交。

用法:  python push_via_api.py [分支名, 默认 main]
"""

import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

REPO = "whlle-yi/campus-proxy-guard"


def gh_token() -> str:
    # 只禁终端提示; 不设 GCM_INTERACTIVE=never(部分 GCM 版本会因此拒绝返回已存凭据)。
    # 无凭据时 GCM 会弹出登录窗口, 由用户完成授权。
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        r = subprocess.run(["git", "credential", "fill"],
                           input="protocol=https\nhost=github.com\n\n",
                           capture_output=True, text=True, timeout=180, env=env)
    except subprocess.TimeoutExpired:
        sys.exit("等待 GitHub 授权超时(GCM 登录窗口未完成), 请重试")
    for line in r.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    sys.exit("未找到 GitHub 凭据, 请先 git push 一次让凭据管理器保存 token")


def call(url, token, payload=None, method=None):
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }, data=json.dumps(payload).encode("utf-8") if payload is not None else None,
       method=method or ("POST" if payload is not None else "GET"))
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main() -> int:
    branch = sys.argv[1] if len(sys.argv) > 1 else "main"
    token = gh_token()
    api = f"https://api.github.com/repos/{REPO}/git"

    files = subprocess.check_output(["git", "ls-files"], text=True).split()
    print(f"待推送 {len(files)} 个文件 -> {REPO}:{branch}")

    tree_entries = []
    for f in files:
        blob = call(f"{api}/blobs", token, {
            "content": base64.b64encode(open(f, "rb").read()).decode(), "encoding": "base64"})
        tree_entries.append({"path": f, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    tree = call(f"{api}/trees", token, {"tree": tree_entries})

    parent = call(f"{api}/ref/heads/{branch}", token)["object"]["sha"]

    # 幂等: 远端最新提交的内容树与本地一致时无需推送, 避免产生重复快照
    if call(f"{api}/commits/{parent}", token)["tree"]["sha"] == tree["sha"]:
        print("远端已是最新内容, 跳过推送")
        return 0

    message = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True)
    commit = call(f"{api}/commits", token, {"message": message, "tree": tree["sha"],
                                            "parents": [parent]})

    call(f"{api}/refs/heads/{branch}", token, {"sha": commit["sha"], "force": False},
         method="PATCH")
    print(f"已推送: {parent[:10]} -> {commit['sha'][:10]} (快照提交)")
    print(f"查看: https://github.com/{REPO}/commit/{commit['sha']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API 错误 {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
