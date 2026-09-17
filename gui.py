from __future__ import annotations

import queue
import re
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from vocab_collector.collector import Collector
from vocab_collector.config import Config, load_env_file
from vocab_collector.enrich import Enricher
from vocab_collector.exporter import write_xlsx
from vocab_collector.zotero import ZoteroClient, ZoteroError


ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "ZoteroVocabCollector"


def safe_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]+', "_", value).strip().rstrip(".")
    return (value[:100] or "Zotero生词表") + ".xlsx"


class VocabApp(tk.Tk):
    def __init__(self):
        super().__init__()
        load_env_file(ROOT / ".env")
        load_env_file(DATA_DIR / ".env")
        self.config_data = Config.from_environment()
        self.zotero = ZoteroClient()
        self.events = queue.Queue()
        self.paper_rows = []
        self.output_manually_selected = False
        self.title("Zotero 生词整理器")
        self.geometry("920x620")
        self.minsize(760, 500)
        self._build_ui()
        self.after(100, self._drain_events)
        self.after(150, self._load_library)

    def _build_ui(self):
        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Zotero 生词整理器", font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text=f"选择一个 Zotero 分组和一篇论文，仅导出蓝色高亮（{self.config_data.highlight_color}）。",
        ).pack(anchor="w", pady=(4, 14))

        chooser = ttk.Panedwindow(outer, orient="horizontal")
        chooser.pack(fill="both", expand=True)
        left = ttk.Labelframe(chooser, text="1. 选择分组", padding=8)
        right = ttk.Labelframe(chooser, text="2. 选择论文", padding=8)
        chooser.add(left, weight=1)
        chooser.add(right, weight=2)

        self.collection_tree = ttk.Treeview(left, show="tree", selectmode="browse")
        self.collection_tree.pack(fill="both", expand=True)
        self.collection_tree.bind("<<TreeviewSelect>>", self._on_collection_selected)

        paper_scroll = ttk.Scrollbar(right, orient="vertical")
        self.paper_list = tk.Listbox(
            right, exportselection=False, font=("Microsoft YaHei UI", 10),
            activestyle="dotbox", yscrollcommand=paper_scroll.set,
        )
        paper_scroll.config(command=self.paper_list.yview)
        paper_scroll.pack(side="right", fill="y")
        self.paper_list.pack(side="left", fill="both", expand=True)
        self.paper_list.bind("<<ListboxSelect>>", self._on_paper_selected)

        output = ttk.Labelframe(outer, text="3. 选择输出位置", padding=10)
        output.pack(fill="x", pady=(14, 8))
        self.output_var = tk.StringVar()
        ttk.Entry(output, textvariable=self.output_var).pack(side="left", fill="x", expand=True)
        ttk.Button(output, text="浏览…", command=self._choose_output).pack(side="left", padx=(8, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(6, 0))
        self.progress = ttk.Progressbar(actions, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)
        self.run_button = ttk.Button(actions, text="开始整理并导出 Excel", command=self._start_export)
        self.run_button.pack(side="left", padx=(12, 0))
        self.status_var = tk.StringVar(value="正在连接 Zotero…")
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(8, 0))
        ttk.Label(
            outer,
            text="翻译会发送高亮文字至 MyMemory。Zotero 数据、PDF 原句和 Excel 文件均保存在本机。",
            foreground="#666666",
            wraplength=850,
        ).pack(anchor="w", pady=(5, 0))

    def _load_library(self):
        try:
            self.zotero.status()
            collections = self.zotero.collections()
        except ZoteroError as exc:
            self.status_var.set(str(exc))
            messagebox.showerror("无法读取 Zotero", str(exc))
            return
        self.collection_tree.insert("", "end", iid="__library__", text="我的文库", open=True)
        pending = {item.get("data", item)["key"]: item.get("data", item) for item in collections}
        while pending:
            progressed = False
            for key, data in list(pending.items()):
                parent_key = data.get("parentCollection") or "__library__"
                if self.collection_tree.exists(parent_key):
                    self.collection_tree.insert(parent_key, "end", iid=key, text=data.get("name") or "未命名分组")
                    del pending[key]
                    progressed = True
            if not progressed:
                for key, data in pending.items():
                    self.collection_tree.insert("__library__", "end", iid=key, text=data.get("name") or "未命名分组")
                break
        self.collection_tree.selection_set("__library__")
        self.collection_tree.focus("__library__")
        self._load_papers(None)

    def _on_collection_selected(self, _event=None):
        selection = self.collection_tree.selection()
        if selection:
            self._load_papers(None if selection[0] == "__library__" else selection[0])

    def _load_papers(self, collection_key):
        self.paper_list.delete(0, "end")
        try:
            raw_items = self.zotero.papers(collection_key)
        except ZoteroError as exc:
            messagebox.showerror("读取失败", str(exc))
            return
        self.paper_rows = []
        for item in sorted(raw_items, key=lambda value: (value.get("data", value).get("title") or "").casefold()):
            data = item.get("data", item)
            title = (data.get("title") or "未命名论文").strip()
            self.paper_rows.append((data.get("key") or item.get("key"), title))
            self.paper_list.insert("end", title)
        self.status_var.set(f"当前分组共有 {len(self.paper_rows)} 篇论文")

    def _on_paper_selected(self, _event=None):
        selected = self.paper_list.curselection()
        if selected and not self.output_manually_selected:
            desktop = Path.home() / "Desktop"
            self.output_var.set(str(desktop / safe_filename(self.paper_rows[selected[0]][1])))

    def _choose_output(self):
        selected = self.paper_list.curselection()
        default_name = safe_filename(self.paper_rows[selected[0]][1]) if selected else "Zotero生词表.xlsx"
        path = filedialog.asksaveasfilename(
            title="选择 Excel 输出位置", defaultextension=".xlsx",
            filetypes=[("Excel 工作簿", "*.xlsx")], initialfile=default_name,
        )
        if path:
            self.output_var.set(path)
            self.output_manually_selected = True

    def _start_export(self):
        selected = self.paper_list.curselection()
        if not selected:
            messagebox.showwarning("尚未选择论文", "请先选择一篇论文。")
            return
        if not self.output_var.get().strip():
            messagebox.showwarning("尚未选择位置", "请选择 Excel 输出位置。")
            return
        paper_key, title = self.paper_rows[selected[0]]
        output = Path(self.output_var.get().strip())
        self.run_button.config(state="disabled")
        self.progress["value"] = 0
        self.status_var.set("正在读取所选论文的蓝色高亮…")
        threading.Thread(target=self._export_worker, args=(paper_key, title, output), daemon=True).start()

    def _export_worker(self, paper_key, title, output):
        try:
            rows = Collector(self.zotero, self.config_data.highlight_color).collect(paper_key)
            total = len(rows)
            if not rows:
                self.events.put(("empty", title))
                return
            enricher = Enricher(self.config_data.mymemory_email, DATA_DIR / "enrichment-cache.json")
            enriched = []
            for index, row in enumerate(rows, 1):
                enriched.append(enricher.enrich(row))
                self.events.put(("progress", index, total))
            write_xlsx(enriched, output)
            review = sum(row.context_status != "ok" for row in enriched)
            self.events.put(("done", output, total, review))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _drain_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "progress":
                    _, current, total = event
                    self.progress["value"] = current * 100 / total
                    self.status_var.set(f"正在翻译和整理：{current}/{total}")
                elif event[0] == "done":
                    _, output, total, review = event
                    self.run_button.config(state="normal")
                    self.status_var.set(f"完成：已导出 {total} 条，{review} 条上下文需核对")
                    messagebox.showinfo("导出完成", f"已保存 {total} 条记录到：\n{output}\n\n其中 {review} 条上下文建议核对。")
                elif event[0] == "empty":
                    self.run_button.config(state="normal")
                    self.status_var.set("所选论文没有蓝色高亮")
                    messagebox.showinfo("没有可导出的高亮", f"《{event[1]}》中没有蓝色高亮。")
                elif event[0] == "error":
                    self.run_button.config(state="normal")
                    self.status_var.set("导出失败")
                    messagebox.showerror("导出失败", event[1])
        except queue.Empty:
            pass
        self.after(100, self._drain_events)


if __name__ == "__main__":
    VocabApp().mainloop()
