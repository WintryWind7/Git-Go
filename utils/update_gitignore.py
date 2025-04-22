import subprocess
from pathlib import Path
from .git_repo import get_repo_info

def update_gitignore():
    """更新.gitignore文件，排除Git-Go仓库"""
    repo = get_repo_info()
    
    # 如果不是Git仓库或是Git-Go自身则跳过
    if not repo.is_repo or repo.is_project_repo:  # 使用正确的属性名
        return
    
    gitignore_path = repo.root_path / ".gitignore"
    target_entry = "/Git-Go/\n"
    
    # 检查是否已存在该条目
    if gitignore_path.exists():
        with open(gitignore_path, 'r+') as f:
            content = f.read()
            if target_entry in content:
                return
            f.write(f"\n{target_entry}")
    else:
        with open(gitignore_path, 'w') as f:
            f.write(target_entry)
    
    print(f"已更新 {gitignore_path} 排除Git-Go仓库")

if __name__ == "__main__":
    update_gitignore()