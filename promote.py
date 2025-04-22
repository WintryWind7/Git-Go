import subprocess
import questionary
import re
import sys
import tempfile
import os
from utils.git_repo import get_repo_info

def get_remote_branch_version(repo_root, branch):
    """更可靠地获取远程分支版本号"""
    try:
        original_dir = os.getcwd()
        os.chdir(repo_root)
        
        # 1. 先检查远程分支是否存在
        remote_refs = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch],
            capture_output=True, text=True
        ).stdout.strip()
        
        if not remote_refs:
            return None
            
        # 2. 直接从远程获取提交信息（不依赖本地对象）
        commit_hash = remote_refs.split()[0]
        commit_info = subprocess.run(
            ["git", "fetch", "origin", f"{branch}:refs/remotes/origin/{branch}", "--quiet"],
            capture_output=True, text=True
        )
        
        # 3. 使用git show获取提交信息（现在本地有对象了）
        commit_msg = subprocess.run(
            ["git", "show", "-s", "--format=%B", commit_hash],
            capture_output=True, text=True
        ).stdout.strip()
        
        # 4. 提取版本号
        first_line = commit_msg.split('\n')[0]
        version_match = re.search(r'(v\d+\.\d+\.\d+)(?:-(dev|beta)\.\d+)?', first_line)
        
        return version_match.group(0) if version_match else None
        
    except Exception as e:
        print(f"⚠️ 获取分支 {branch} 版本时出错: {str(e)}")
        return None
    finally:
        os.chdir(original_dir)


def promote():
    print("🚀 远程分支复制工具 (不操作本地文件)")
    
    # 获取仓库信息
    repo_info = get_repo_info()
    if not repo_info.is_repo or not repo_info.remote_url:
        print("❌ 当前目录不是Git仓库或没有远程仓库")
        return
    
    # 获取各分支当前版本
    dev_version = get_remote_branch_version(repo_info.root_path, "dev")
    beta_version = get_remote_branch_version(repo_info.root_path, "beta")
    
    # 准备选择项
    choices = []
    
    if dev_version:
        # 如果beta分支已存在，则递增beta版本号
        if beta_version and beta_version.startswith(dev_version.split('-dev')[0]):
            current_beta_num = int(beta_version.split('.')[-1])
            new_version = re.sub(r'-dev\.\d+', f'-beta.{current_beta_num + 1}', dev_version)
        else:
            new_version = re.sub(r'-dev\.\d+', '-beta.1', dev_version)
        
        choices.append({
            "name": f"dev({dev_version}) → beta({new_version})",
            "value": ("dev", "beta", dev_version, new_version)
        })
    
    if beta_version:
        new_version = re.sub(r'-beta\.\d+', '', beta_version)
        choices.append({
            "name": f"beta({beta_version}) → main({new_version})",
            "value": ("beta", "main", beta_version, new_version)
        })
    
    if not choices:
        print("❌ 没有可用的分支或无法获取版本号")
        return
    
    # 选择复制方向
    action = questionary.select(
        "选择复制方向:",
        choices=choices
    ).ask()

    if not action:
        print("🚫 操作取消")
        return

    from_branch, to_branch, old_version, new_version = action

    # 确认操作
    print(f"\n🔄 即将执行以下操作：")
    print(f"• 从分支: {from_branch}({old_version})")
    print(f"• 复制到分支: {to_branch}({new_version})")
    if not questionary.confirm("确认继续?").ask():
        print("🚫 操作取消")
        return

    # 执行操作
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            print(f"⚡ 正在克隆仓库到临时目录...")
            subprocess.run(
                ["git", "clone", repo_info.remote_url, tmp_dir],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            # 切换到目标分支（如果存在）
            subprocess.run(
                ["git", "checkout", to_branch],
                cwd=tmp_dir, stderr=subprocess.PIPE  # 允许分支不存在
            )
            
            # 拉取最新代码
            subprocess.run(
                ["git", "pull", "origin", to_branch],
                cwd=tmp_dir, stderr=subprocess.PIPE  # 允许分支不存在
            )
            
            # 合并源分支（保留历史记录）
            print(f"⚡ 正在合并 {from_branch} 到 {to_branch}...")
            subprocess.run(
                ["git", "merge", "--no-ff", f"origin/{from_branch}", "-m", f"{new_version}\n\nupdate from\n{old_version}"],
                cwd=tmp_dir, check=True
            )
            
            # 推送（不使用 --force）
            print(f"⚡ 正在推送到 {to_branch}...")
            push_result = subprocess.run(
                ["git", "push", "origin", to_branch],
                cwd=tmp_dir, capture_output=True, text=True, check=True
            )
            
            print(f"\n✅ 操作成功完成（保留历史记录）")
            print(f"• 已合并: {from_branch}@{old_version} → {to_branch}@{new_version}")
            print(f"• 提交信息:\n{new_version}\n\nupdate from\n{old_version}")

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if isinstance(e.stderr, str) else e.stderr.decode('utf-8') if e.stderr else str(e)
        print(f"\n❌ 操作失败: {error_msg.strip()}")
        if "Your local changes" in error_msg:
            print("💡 提示：请确保目标分支没有未提交的更改")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    promote()
