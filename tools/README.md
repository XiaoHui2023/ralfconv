# 打包工具

本仓库 **不** 在 Git push 时自动打包，GitHub 上 **无** 预编译 Release。clone 后在仓库根本地执行下列命令即可得到 `dist/` 产物。

## 一键打包（PyInstaller；Linux 再 staticx）

在仓库根执行（使用根目录 `.venv`，无则创建）。每次打包会 `--force-reinstall` 重装 `pyproject.toml` 依赖与 PyInstaller，避免 `.venv` 残留旧版依赖。

### Linux / macOS / Git Bash

```bash
./tools/pack.sh
```

### Windows

```bat
tools\pack.bat
```

无法直接执行 `pack.sh` 时，也可用 Git Bash：`bash tools/pack.sh`。

产物写入 `dist/`：

| 目标 | 产物 |
| --- | --- |
| 主入口（src） | `ralfconv` / `ralfconv.exe` |
| 发布压缩包 | `ralfconv-<version>-linux.tar.gz` / `ralfconv-<version>-windows.zip` |

| 平台 | 脚本 | staticx |
| --- | --- | --- |
| Linux | `pack.sh` | 需要系统 **patchelf** |
| macOS 等 | `pack.sh` | 跳过 |
| Windows | `pack.bat` / `pack.sh` | 跳过 |
