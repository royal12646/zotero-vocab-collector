# Zotero 生词整理器

一个面向 Windows 和 Zotero 的本地桌面工具。选择一篇论文后，程序会收集其中的**蓝色高亮**，补充中文翻译，并导出为带格式的 Excel 生词表。

## 功能

- 按 Zotero 文件夹浏览论文，并且一次只整理一篇论文。
- 只收集 Zotero 默认蓝色高亮（`#2ea8e5`）。
- 获取一个词的常用义和多个候选释义。
- 从本地 PDF 恢复高亮所在原句。
- 在原句中用红色粗体标出陌生词汇，忽略大小写并标记所有匹配项。
- Excel 包含“陌生词汇、翻译、所在原句、论文、页码”五列，带表头配色、边框、自动换行和筛选。
- 输出文件默认使用论文标题命名。

## 系统要求

- Windows 10 或 Windows 11
- Zotero 桌面端（已在 Zotero 9.0.6 上验证）
- Zotero 中的论文具有本地 PDF 附件
- 使用翻译功能时需要联网

## 下载与安装

1. 打开本仓库的 [Releases 页面](https://github.com/royal12646/zotero-vocab-collector/releases)。
2. 下载最新版本的 `Zotero生词整理器.exe`。
3. 将程序放在桌面或任意文件夹，无需安装。
4. 如果 Windows SmartScreen 提示未知发布者，请确认文件来自本仓库的 Releases 页面，再选择“更多信息 → 仍要运行”。

> 程序当前没有代码签名，因此 Windows 可能显示安全提示。

## 首次设置 Zotero

1. 启动 Zotero。
2. 打开“编辑 → 设置 → 高级”。
3. 勾选“允许本机其他应用与 Zotero 通信”。
4. 保持 Zotero 运行，然后启动本程序。

## 使用方法

1. 在 Zotero PDF 阅读器中，用**蓝色**高亮标记陌生单词、短语或句子。
2. 双击 `Zotero生词整理器.exe`。
3. 在左侧选择 Zotero 文件夹分组。
4. 在右侧选择一篇论文。
5. 选择 Excel 输出位置；默认文件名为论文标题。
6. 点击“开始整理并导出 Excel”。

输出工作簿包含：

| 列名 | 内容 |
| --- | --- |
| 陌生词汇 | Zotero 中的蓝色高亮文字 |
| 翻译 | 常用义和其他候选释义 |
| 所在原句 | 从 PDF 恢复的原句，生词显示为红色粗体 |
| 论文 | Zotero 条目标题 |
| 页码 | Zotero 标注页码 |

## 数据与隐私

- Zotero 文库信息和 PDF 原句均通过本机接口读取。
- Excel 只保存到你选择的本地位置，不上传到 Airtable 或其他表格服务。
- 为生成中文翻译，**高亮文字会发送到 MyMemory 翻译服务**。
- 翻译缓存保存在 `%LOCALAPPDATA%\ZoteroVocabCollector\enrichment-cache.json`。
- 仓库和发布包不包含你的 Zotero 数据库、PDF、标注、翻译缓存或个人令牌。

## 常见问题

### 程序显示“无法连接 Zotero”

确认 Zotero 正在运行，并已开启“允许本机其他应用与 Zotero 通信”。

### 找不到论文或文件夹

关闭并重新打开程序以刷新文库。如果条目只是独立 PDF，没有标准的父级文献条目，请先在 Zotero 中为它创建父条目。

### 提示“所选论文没有蓝色高亮”

程序只读取颜色值为 `#2ea8e5` 的 Zotero 蓝色高亮。其他颜色不会导出。

### 原句内容不准确

程序会在对应 PDF 页面中搜索高亮文字。如果同一词在页面中出现多次，会使用第一个匹配；扫描版 PDF 可能需要先进行 OCR。

### 翻译为空

检查网络连接。MyMemory 免费接口可能有调用频率或每日额度限制，稍后重试即可。

## 测试与构建 Windows 程序

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean "Zotero生词整理器.spec"
```

构建结果位于 `dist\Zotero生词整理器.exe`。

## 项目结构

```text
gui.py                    桌面界面入口
main.py                   命令行诊断与导出入口
vocab_collector/          Zotero 读取、PDF 原句恢复、翻译和 Excel 导出
tests/                    自动测试
.env.example              可选配置示例
Zotero生词整理器.spec      PyInstaller 构建配置
```

## 当前限制

- 仅支持 Zotero 本地文库，不读取 Zotero Web Library。
- 仅针对英文高亮提供英译中。
- 扫描版 PDF 的原句恢复依赖 PDF 已包含可搜索文本。
