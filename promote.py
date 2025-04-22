import subprocess
import questionary

def promote():
    print("🚀 直接版本复制工具")
    
    # 选择复制方向
    action = questionary.select(
        "选择复制方向:",
        choices=[
            {"name": "dev → beta", "value": ("dev", "beta")},
            {"name": "beta → main", "value": ("beta", "main")}
        ]
    ).ask()

    if not action:
        return

    from_branch, to_branch = action

    # 获取最新dev提交
    latest_commit = subprocess.run(
        ["git", "log", "-1", "--pretty=%H", f"origin/{from_branch}"],
        capture_output=True,
        text=True
    ).stdout.strip()

    if not latest_commit:
        print("❌ 无法获取最新提交")
        return

    # 获取提交信息
    commit_msg = subprocess.run(
        ["git", "log", "-1", "--pretty=%B", latest_commit],
        capture_output=True,
        text=True
    ).stdout.strip()

    # 转换版本号
    first_line = commit_msg.split('\n')[0]
    version = first_line.split()[0]  # 获取原始版本号
    
    if to_branch == "beta":
        new_version = version.replace("-dev", "-beta")
    elif to_branch == "main":
        new_version = version.split("-")[0]  # 移除后缀

    # 获取用户输入
    title = questionary.text("输入新标题:").ask() or f"Promote to {to_branch}"
    desc = questionary.text("输入新描述:").ask() or commit_msg

    # 执行复制（强制覆盖）
    commands = [
        ["git", "checkout", to_branch],
        ["git", "reset", "--hard", latest_commit],
        ["git", "commit", "--amend", "-m", f"{new_version} {title}\n\n{desc}"],
        ["git", "push", "origin", to_branch, "--force"]
    ]

    for cmd in commands:
        print(f"⚡ 执行: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("❌ 执行失败")
            return

    print(f"✅ 已强制将 {from_branch} 的 {version} 复制为 {new_version} 到 {to_branch}")

if __name__ == "__main__":
    promote()