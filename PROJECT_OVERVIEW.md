# Stardew Save Editor 项目概览 (Python 桌面版)

## 1. 项目简介
本项目是一个功能强大的《星露谷物语》（Stardew Valley）桌面端存档编辑器。它允许玩家在本地直接读取并修改游戏存档文件，提供直观的 GUI 界面来调整角色属性、管理背包物品、修改社交关系以及解锁游戏进度。

## 2. 核心功能
项目实现了对游戏存档（XML 格式）的深度解析与修改，主要功能包括：
- **角色管理**：修改名称、外观（发型、衣服、配件等）、技能等级、职业选择、金钱、齐钻、黄金核桃等。
- **背包与储物箱**：添加、删除或修改物品的数量、品质。完全支持 1.6 版本的新物品格式。
- **社交关系**：查看并修改与所有 NPC 的好感度。
- **进度解锁**：解锁烹饪配方、打造配方、成就、特殊能力（如姜岛进度）。
- **存档管理**：自动扫描游戏存档目录，修改前自动备份。

## 3. 技术栈
项目采用 Python 栈开发，旨在提供轻量级且功能完备的本地工具：
- **语言**: Python 3.11+
- **GUI 框架**: `tkinter` + `ttkbootstrap` (提供现代化、可换肤的主题界面)。
- **数据解析**: `xml.etree.ElementTree` (用于高效处理游戏 XML 存档)。
- **图像处理**: `Pillow` (用于处理图标和基础视觉资源)。
- **打包**: `PyInstaller` (支持将 Python 脚本打包为独立的 Windows `.exe` 可执行文件)。

## 4. 目录结构
```text
stardew-save-editor-main/
├── generated/            # 游戏原始数据备份 (JSON)
│   └── iteminfo.json     # 全量物品信息
├── modifier/             # Python 核心源码
│   ├── i18n/             # 多语言支持 (中/英)
│   ├── models/           # 数据代理模型 (存档结构的 Python 类映射)
│   ├── ui/               # Tkinter 界面代码与组件
│   ├── utils/            # 工具函数 (存档读写、翻译、物品管理)
│   └── main.py           # 程序主入口
├── sync_items.py         # 数据同步脚本 (从 generated/ 更新 models/item_data.py)
├── build_exe.py          # 打包脚本
└── requirements.txt      # Python 依赖清单
```

## 5. 关键设计模式
### 数据代理 (Proxy Pattern)
项目在 `modifier/models` 中大量使用了代理模式。每个模型类（如 `Farmer`, `Item`, `Inventory`）都封装了一个原始的 XML 节点对象。通过这种方式，对模型属性的修改会直接反映到 XML 结构中，确保了数据的一致性和保存时的准确性。

## 6. 开发与打包
- **运行**: `python modifier/main.py`
- **数据更新**: 如果游戏版本更新或 `generated/` 数据有变，运行 `python sync_items.py`。
- **打包**: 运行 `python build_exe.py` 生成分发版。

## 7. 兼容性
- 核心支持 **Stardew Valley 1.6** 版本存档。
- 仅支持 **Windows** 操作系统。
