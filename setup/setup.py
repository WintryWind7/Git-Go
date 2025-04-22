import os
import json
from pathlib import Path
from rich import print
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

console = Console()

def get_config_path() -> Path:
    """返回配置文件的完整路径（Windows优先用AppData）"""
    if os.name == "nt":
        return Path(os.getenv("APPDATA")) / "Git-Go" / "git-go.cfg"
    else:
        return Path.home() / ".config" / "git-go" / "git-go.cfg"

def init_default_config() -> dict:
    """生成默认配置（仅包含您需要的字段）"""
    return {
        "branches": {
            "MAIN": "main",
            "BETA": "beta",
            "DEV": "dev"
        },
        "force": False  # 唯一新增字段（用户可选的强制模式）
    }

def upgrade_config(config: dict) -> dict:
    """兼容旧配置（确保包含所有必要字段）"""
    if "force" not in config:  # 如果旧配置缺少force字段
        config["force"] = False  # 添加默认值
    return config

def show_config_table(config: dict):
    """用表格展示当前配置"""
    table = Table(title="当前配置", show_header=False, border_style="blue")
    table.add_column("Key", style="cyan", justify="right")
    table.add_column("Value", style="magenta")
    
    # 分支信息
    for branch, name in config["branches"].items():
        table.add_row(branch, name)
    
    # Force模式状态
    force_status = "[green]ON" if config["force"] else "[red]OFF"
    table.add_row("FORCE MODE", force_status)
    
    console.print(table)

def setup_config():
    """配置初始化主逻辑"""
    cfg_path = get_config_path()
    
    # 标题
    console.print(Panel.fit("🎯 [bold blue]Git-Go 配置初始化工具[/]", border_style="blue"))
    console.print(f"📂 配置文件路径: [cyan underline]{cfg_path}[/]")

    # 如果配置文件已存在
    if cfg_path.exists():
        with open(cfg_path) as f:
            config = upgrade_config(json.load(f))  # 确保配置兼容
        console.print("[green]✅ 配置文件已加载[/]")
        show_config_table(config)
        return
    
    # 创建新配置
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    default_cfg = init_default_config()
    with open(cfg_path, 'w') as f:
        json.dump(default_cfg, f, indent=2)
    
    console.print("[yellow]🆕 已创建默认配置:[/]")
    show_config_table(default_cfg)
    console.print("\n[dim]提示: 直接编辑此文件可修改配置[/]")

if __name__ == "__main__":
    setup_config()