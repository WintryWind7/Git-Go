import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def load_module(module_name, module_path):
    """安全的动态模块加载"""
    module_path = Path(module_path).absolute()
    if not module_path.exists():
        raise ImportError(f"模块文件不存在: {module_path}")
    
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"无法创建模块规范: {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 动态加载git_repo模块
current_script_path = Path(__file__).absolute()
utils_dir = current_script_path.parent.parent / "utils"
git_repo_path = utils_dir / "git_repo.py"

try:
    git_repo = load_module("git_repo", git_repo_path)
    get_repo_info = git_repo.get_repo_info
    check_remote_connection = git_repo.check_remote_connection
except ImportError as e:
    console.print(f"[red]错误: 无法加载git_repo模块[/]\n{str(e)}")
    sys.exit(1)

def check_git_installed() -> bool:
    """检查Git是否安装"""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def show_check_result(results: dict):
    """用表格展示检查结果"""
    table = Table(title="🔍 Git 连接状态检查", show_header=False, border_style="blue")
    table.add_column("检查项", style="cyan", width=25)
    table.add_column("状态", style="magenta")
    
    for item, (status, msg) in results.items():
        status_icon = "[green]✓" if status else "[red]✗"
        table.add_row(item, f"{status_icon} {msg}")
    
    console.print(table)

def check_git():
    """主检查逻辑"""
    # console.print(Panel.fit("🛠️ Git 基础连接检查工具", style="bold blue")) # 不好看
    results = {}
    
    # 1. 检查Git安装
    git_installed = check_git_installed()
    results["Git安装"] = (
        git_installed,
        "已安装" if git_installed else "未安装或未配置PATH"
    )
    
    # 2. 使用动态加载的模块检查仓库状态
    repo_info = get_repo_info()
    results["Git仓库"] = (
        repo_info.is_repo,
        str(repo_info.root_path) if repo_info.is_repo else "当前目录不是Git仓库"
    )
    
    # 3. 检查远程连接（仅在仓库内检查）
    remote_ok = False
    if repo_info.is_repo:
        remote_ok = check_remote_connection()
        results["远程连接"] = (
            remote_ok,
            "连接正常" if remote_ok else "无法连接到远程仓库"
        )
    
    # 4. 显示项目/开发模式
    if repo_info.is_repo:
        mode = "项目模式 (/project)" if repo_info.is_project_repo else "开发模式 (/git-go)"
        results["运行模式"] = (True, mode)
    
    # 显示结果
    show_check_result(results)
    console.print("\n[dim]提示: 请确保网络畅通且有仓库访问权限[/]")

if __name__ == "__main__":
    check_git()