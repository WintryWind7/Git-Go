import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List

class BranchManager:
    def __init__(self):
        self.config_path = self._get_config_path()
        self.repo_root = self._get_repo_root()

    def _get_config_path(self) -> Path:
        """获取配置文件路径（跨平台）"""
        if os.name == "nt":
            return Path(os.getenv("APPDATA")) / "Git-Go" / "git-go.cfg"
        return Path.home() / ".config" / "git-go" / "git-go.cfg"

    def _get_repo_root(self) -> Path:
        """获取Git仓库根目录"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            raise RuntimeError("当前目录不是Git仓库")

    def _load_branch_config(self) -> Dict[str, str]:
        """加载分支配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path) as f:
            config = json.load(f)

        if "branches" not in config:
            raise ValueError("配置文件中缺少branches字段")
        
        return config["branches"]

    def _get_remote_branches(self) -> List[str]:
        """获取所有远程分支列表"""
        result = subprocess.run(
            ["git", "branch", "-r"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        return [
            b.strip().replace("origin/", "")
            for b in result.stdout.splitlines()
            if "->" not in b
        ]

    def check_missing_branches(self) -> List[str]:
        """检测缺失的分支"""
        required = self._load_branch_config().values()
        existing = self._get_remote_branches()
        return [b for b in required if b not in existing]

    def create_branch(self, branch_name: str):
        """创建并推送新分支"""
        try:
            # 创建本地分支
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_root,
                check=True
            )
            # 推送到远程
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=self.repo_root,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"创建分支 {branch_name} 失败: {e.stderr}")
            return False

    def sync_branches(self):
        """同步所有配置的分支"""
        missing = self.check_missing_branches()
        if not missing:
            print("✅ 所有配置分支已存在")
            return

        print(f"需创建分支: {', '.join(missing)}")
        for branch in missing:
            if self.create_branch(branch):
                print(f"  已创建: {branch}")

def sync_branches():
    try:
        manager = BranchManager()
        manager.sync_branches()
        return True
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


if __name__ == "__main__":
    sync_branches()