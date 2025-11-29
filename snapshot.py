import os
from pathlib import Path

# 配置：需要读取的文件夹和后缀
INCLUDE_DIRS = [".specgraph", "devspec"]
INCLUDE_EXTS = {".yaml", ".py", ".md", ".toml"}
IGNORE_DIRS = {"__pycache__", ".venv", ".git", ".devspec"}

def generate_snapshot():
    output = []
    root = Path(".")
    
    output.append("# PROJECT SNAPSHOT")
    output.append(f"Root: {root.resolve().name}\n")
    
    # 1. 先打印目录树结构
    output.append("## 1. Directory Structure")
    for path in sorted(root.rglob("*")):
        # 过滤忽略的目录
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.is_dir():
            depth = len(path.relative_to(root).parts)
            indent = "  " * (depth - 1)
            output.append(f"{indent}📂 {path.name}/")
        elif path.suffix in INCLUDE_EXTS:
            depth = len(path.relative_to(root).parts)
            indent = "  " * (depth - 1)
            output.append(f"{indent}📄 {path.name}")

    # 2. 打印文件内容
    output.append("\n## 2. File Contents")
    for path in sorted(root.rglob("*")):
        # 过滤忽略的目录
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        
        # 只读取特定后缀的文件
        if path.is_file() and path.suffix in INCLUDE_EXTS:
            # 排除 snapshot.py 自己
            if path.name == "snapshot.py": 
                continue
                
            output.append(f"\n--- START OF FILE {path} ---")
            try:
                content = path.read_text(encoding="utf-8")
                output.append(content)
            except Exception as e:
                output.append(f"(Error reading file: {e})")
            output.append(f"--- END OF FILE {path} ---\n")

    return "\n".join(output)

if __name__ == "__main__":
    import pyperclip
    try:
        snapshot = generate_snapshot()
        pyperclip.copy(snapshot)
        print("✅ 项目快照已复制到剪贴板！(约 {} 字符)".format(len(snapshot)))
        print("👉 请直接粘贴给 AI。")
    except ImportError:
        print(generate_snapshot())
        print("\n(未安装 pyperclip，请手动复制以上内容)")