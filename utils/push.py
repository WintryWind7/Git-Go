import subprocess
import re
import tempfile
import sys
import os
import shutil
from typing import Optional, Tuple

class FinalVersionManager:
    def __init__(self):
        self.remote_url = self._get_remote_url()
        self.current_version = self._fetch_actual_version()
        if not self.current_version:
            print("❌ 错误：无法获取远程dev分支版本")
            print("请确认：")
            print("1. 远程存在dev分支")
            print("2. 最新提交格式为 vX.Y.Z 或 vX.Y.Z-dev.N")
            sys.exit(1)

    def _get_remote_url(self) -> str:
        """获取远程地址（失败则退出）"""
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("❌ 无法获取远程地址")
            sys.exit(1)
        return result.stdout.strip()

    def _fetch_actual_version(self) -> Optional[Tuple[int, int, int, int]]:
        """增强版版本号获取，解决空返回问题"""
        try:
            # 1. 检查本地是否有远程分支缓存
            subprocess.run(["git", "fetch", "origin", "dev"], 
                        capture_output=True, check=True)
            
            # 2. 获取提交信息（不使用ls-remote，直接使用本地缓存）
            result = subprocess.run(
                ["git", "log", "origin/dev", "-1", "--pretty=%B"],
                capture_output=True, text=True
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                print("❌ 无法获取dev分支提交信息")
                print(f"Git错误: {result.stderr.strip()}")
                return None

            commit_msg = result.stdout.strip()
            print(f"✅ 获取到的提交信息: '{commit_msg}'")  # 调试输出

            # 3. 优化版正则匹配
            pattern = r'''
                ^               # 行首
                v               # v前缀
                (\d+)\.(\d+)\.(\d+)  # 主版本号
                (?:-dev\.(\d+))?     # 可选dev版本
                (?:\s|$)        # 空格或行尾
            '''
            match = re.search(pattern, commit_msg.splitlines()[0], re.VERBOSE)
            
            if match:
                groups = match.groups()
                return (
                    int(groups[0]),  # major
                    int(groups[1]),  # minor
                    int(groups[2]),  # patch
                    int(groups[3]) if groups[3] else 0  # dev
                )
                
            print(f"❌ 无法解析版本号: '{commit_msg.splitlines()[0]}'")
            return None

        except subprocess.CalledProcessError as e:
            print(f"❌ Git命令执行失败: {e.stderr.decode().strip()}")
            return None
        except Exception as e:
            print(f"❌ 发生意外错误: {str(e)}")
            return None

    def get_version_display(self) -> str:
        """返回显示用的版本字符串"""
        v = self.current_version
        return f"v{v[0]}.{v[1]}.{v[2]}-dev.{v[3]}" if v[3] > 0 else f"v{v[0]}.{v[1]}.{v[2]}"

    def make_next_version(self, input_version: str) -> str:
        """生成下一个正确版本"""
        try:
            if not input_version.startswith('v'):
                input_version = f'v{input_version}'
            
            if match := re.search(r'v(\d+)\.(\d+)\.(\d+)', input_version):
                major, minor, patch = map(int, match.groups())
                
                if (major, minor, patch) == self.current_version[:3]:
                    return f"v{major}.{minor}.{patch}-dev.{self.current_version[3] + 1}"
                return f"v{major}.{minor}.{patch}-dev.1"
            raise ValueError
        except Exception:
            print(f"❌ 非法版本格式: {input_version}")
            sys.exit(1)

    def push_with_power(self, version: str, title: str, desc: str) -> bool:
        """终极强制推送 - 完全用本地文件覆盖远程"""
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                print("🔄 正在准备临时仓库...")
                
                # 1. 克隆仓库（完整克隆）
                subprocess.run(
                    ["git", "clone", self.remote_url, tmp_dir],
                    check=True, capture_output=True
                )
                
                # 2. 检查远程dev分支是否存在
                remote_branch_check = subprocess.run(
                    ["git", "ls-remote", "--heads", "origin", "dev"],
                    cwd=tmp_dir, capture_output=True, text=True
                )
                
                if remote_branch_check.returncode == 0 and remote_branch_check.stdout.strip():
                    # 远程dev分支存在，创建本地跟踪分支
                    print("✅ 检测到远程dev分支")
                    subprocess.run(
                        ["git", "checkout", "-b", "dev", "--track", "origin/dev"],
                        cwd=tmp_dir, check=True
                    )
                else:
                    # 远程dev分支不存在，创建新分支
                    print("⚠️ 远程dev分支不存在，将创建新分支")
                    subprocess.run(
                        ["git", "checkout", "--orphan", "dev"],
                        cwd=tmp_dir, check=True
                    )
                    subprocess.run(
                        ["git", "rm", "-rf", "."],
                        cwd=tmp_dir, check=True
                    )
                    
                # 3. 清空临时仓库（保留.git目录）
                print("🧹 清空临时仓库...")
                for item in os.listdir(tmp_dir):
                    if item != '.git':
                        path = os.path.join(tmp_dir, item)
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.unlink(path)
                
                # 4. 复制本地所有文件（除.git和.gitignore外）
                print("📦 复制本地文件...")
                current_dir = os.getcwd()
                for item in os.listdir(current_dir):
                    if item not in ['.git', '.gitignore']:
                        src = os.path.join(current_dir, item)
                        dst = os.path.join(tmp_dir, item)
                        if os.path.isdir(src):
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src, dst)
                
                # 5. 创建强制提交
                print("💾 创建提交...")
                subprocess.run(["git", "add", "."], cwd=tmp_dir, check=True)
                
                # 检查是否有更改需要提交
                status_check = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=tmp_dir, capture_output=True, text=True
                )
                if not status_check.stdout.strip():
                    print("⚠️ 没有检测到文件变更，将创建空提交")
                
                subprocess.run(
                    ["git", "commit", "--allow-empty", "-m", f"{version} {title}\n\n{desc}"],
                    cwd=tmp_dir, check=True
                )
                
                # 6. 强制推送
                print("🚀 正在强制推送...")
                subprocess.run(
                    ["git", "push", "origin", "dev", "--force"],
                    cwd=tmp_dir, check=True
                )
                
                print("✅ 推送成功！")
                return True
                
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            print(f"❌ Git命令执行失败: {error_msg}")
            return False
        except Exception as e:
            print(f"❌ 推送异常: {str(e)}")
            return False
