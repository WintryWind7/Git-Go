from utils.push import FinalVersionManager
import questionary
import re
import sys
from typing import Tuple

def validate_version(input_version: str, current_version: Tuple[int, int, int, int]) -> bool:
    """简化版验证，只返回布尔值"""
    if not re.match(r'^\d+\.\d+\.\d+$', input_version):
        return False
    
    try:
        input_parts = tuple(map(int, input_version.split('.')))
        current_major, current_minor, current_patch, _ = current_version
        
        if input_parts == (current_major, current_minor, current_patch):
            return True
            
        if input_parts[:2] == (current_major, current_minor):
            return input_parts[2] == current_patch + 1
        elif input_parts[0] == current_major:
            return input_parts[1] == current_minor + 1 and input_parts[2] == 0
        else:
            return input_parts[0] == current_major + 1 and input_parts[1] == 0 and input_parts[2] == 0
                    
    except ValueError:
        return False

def run():
    print("🔥 终极版本控制系统")
    print("=====================================")
    
    manager = FinalVersionManager()
    current_display = manager.get_version_display()
    print(f"当前版本: {current_display}")

    # 简化版输入验证
    base = questionary.text(
        "输入基础版本号:",
        validate=lambda x: validate_version(x, manager.current_version)
    ).ask()
    
    if not base:
        print("🚫 操作取消")
        sys.exit(0)

    next_ver = manager.make_next_version(base)
    print(f"\n🔄 将创建版本: {next_ver}")

    print("\n📝 提交信息:")
    title = questionary.text(
        "标题:", 
        validate=lambda x: bool(x.strip())
    ).ask()
    
    desc = questionary.text("描述:").ask() or "无描述"

    print("\n💣 正在执行终极推送...")
    if manager.push_with_power(next_ver, title, desc):
        print(f"\n✅ 推送成功! 新版本: {next_ver}")
    else:
        print("\n❌ 推送失败")
        sys.exit(1)

if __name__ == "__main__":
    run()
