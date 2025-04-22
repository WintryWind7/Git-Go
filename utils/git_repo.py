import os
import subprocess
from pathlib import Path
from typing import NamedTuple, Optional

class RepoInfo(NamedTuple):
    """Git仓库信息数据类"""
    is_repo: bool
    root_path: Optional[Path]  # 仓库根目录（绝对路径）
    is_project_repo: bool      # 是否在/project目录下
    current_branch: Optional[str]
    remote_url: Optional[str]

def find_git_root(start_path: Path) -> Optional[Path]:
    """
    递归向上查找.git目录
    返回: Git仓库根目录（绝对路径）或None
    """
    current_path = start_path.resolve()  # 转为绝对路径
    while True:
        if (current_path / ".git").exists():
            return current_path
        
        if current_path.parent == current_path:  # 到达根目录
            return None
        
        current_path = current_path.parent

def get_repo_info() -> RepoInfo:
    """
    检测Git仓库状态（优先检查/project目录）
    逻辑：
    1. 先检查/project/.git是否存在
    2. 若不存在，检查/git-go/.git
    3. 若仍不存在，检查当前目录
    """
    # 关键路径定义
    utils_dir = Path(__file__).parent  # /project/git-go/utils
    git_go_dir = utils_dir.parent       # /project/git-go
    project_dir = git_go_dir.parent     # /project
    
    # 按优先级检查可能的仓库根目录
    for possible_root in [project_dir, git_go_dir, Path.cwd()]:
        if (git_root := find_git_root(possible_root)) is not None:
            # 获取仓库信息
            os.chdir(git_root)  # 切换到仓库根目录确保命令执行正确
            
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True
            ).stdout.strip() if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                                              capture_output=True).returncode == 0 else None
            
            remote = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True
            ).stdout.strip() if subprocess.run(["git", "remote"], 
                                             capture_output=True).returncode == 0 else None
            
            return RepoInfo(
                is_repo=True,
                root_path=git_root,
                is_project_repo=(git_root == project_dir),
                current_branch=branch or None,
                remote_url=remote or None
            )
    
    return RepoInfo(False, None, False, None, None)

def check_remote_connection() -> bool:
    """检查远程仓库是否可达（需在仓库内调用）"""
    try:
        subprocess.run(
            ["git", "ls-remote", "origin"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False