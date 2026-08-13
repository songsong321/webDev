import asyncio
import subprocess
import os
import json
import sys
from playwright.async_api import async_playwright

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

INJECTION_SCRIPT = """
(() => {
    if (window.__ai_initialized) return;
    window.__ai_initialized = true;

    window.__ai_annotations = [];

    function injectElements() {
        if (document.getElementById('ai-highlight-box')) return true;
        if (!document.body) return false;

        const highlightBox = document.createElement('div');
        highlightBox.id = 'ai-highlight-box';
        highlightBox.style.cssText = 'display: none; position: fixed; pointer-events: none; border: 3px solid #ff4d4f !important; background: rgba(255, 77, 79, 0.2) !important; z-index: 2147483647 !important; transition: all 0.05s ease; border-radius: 4px; box-sizing: border-box;';
        document.body.appendChild(highlightBox);

        const batchPanel = document.createElement('div');
        batchPanel.id = 'ai-batch-panel';
        batchPanel.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 2147483647; background: #18181b; color: #f4f4f5; padding: 16px; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; box-shadow: 0 10px 30px rgba(0,0,0,0.6); width: 360px; border: 1px solid #27272a; display: none;';
        batchPanel.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #27272a; padding-bottom: 10px;">
                <span style="font-weight: 600; font-size: 13px; color: #22c55e; display: flex; align-items: center; gap: 6px;">
                    <span style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; display: inline-block;"></span>
                    AI 深度逻辑批注看板 (<span id="ai-count">0</span>)
                </span>
                <button id="ai-export-btn" style="background: #22c55e; color: #09090b; border: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">开始深度逻辑重构</button>
            </div>
            <div id="ai-list-container" style="max-height: 200px; overflow-y: auto; font-size: 12px; display: flex; flex-direction: column; gap: 8px; padding-right: 4px;"></div>
        `;
        document.body.appendChild(batchPanel);

        const modal = document.createElement('div');
        modal.id = 'ai-modal-box';
        modal.style.cssText = 'display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.7); z-index: 2147483647; justify-content: center; align-items: center; font-family: -apple-system, BlinkMacSystemFont, sans-serif; backdrop-filter: blur(4px);';
        modal.innerHTML = `
            <div style="background: #18181b; color: #f4f4f5; padding: 24px; border-radius: 14px; width: 500px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); border: 1px solid #27272a;">
                <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #22c55e; font-weight: 600;">🧠 添加逻辑/交互修改批注</h3>
                <p id="ai-target-info" style="font-size: 12px; color: #a1a1aa; margin: 0 0 14px 0; word-break: break-all; line-height: 1.5; background: #09090b; padding: 8px 10px; border-radius: 6px; border: 1px solid #27272a;"></p>
                <textarea id="ai-note-input" placeholder="请详细描述逻辑需求（例如：点击此按钮时跳过账号表单校验，直接模拟成功返回 / 修改绑定的提交方法等）..." style="width: 100%; height: 110px; background: #09090b; color: #f4f4f5; border: 1px solid #27272a; border-radius: 8px; padding: 12px; box-sizing: border-box; resize: none; font-size: 13px; outline: none;"></textarea>
                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px;">
                    <button id="ai-cancel-btn" style="padding: 7px 16px; background: #27272a; color: #a1a1aa; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">取消</button>
                    <button id="ai-submit-btn" style="padding: 7px 16px; background: #22c55e; color: #09090b; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px;">确认添加</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        const confirmModal = document.createElement('div');
        confirmModal.id = 'ai-confirm-modal';
        confirmModal.style.cssText = 'display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.7); z-index: 2147483647; justify-content: center; align-items: center; font-family: -apple-system, BlinkMacSystemFont, sans-serif; backdrop-filter: blur(4px);';
        confirmModal.innerHTML = `
            <div style="background: #18181b; color: #f4f4f5; padding: 24px; border-radius: 14px; width: 400px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); border: 1px solid #27272a; text-align: center;">
                <h3 style="margin: 0 0 10px 0; font-size: 16px; color: #22c55e; font-weight: 600;">✨ 确认开始深度逻辑重构？</h3>
                <p id="ai-confirm-text" style="font-size: 13px; color: #a1a1aa; margin: 0 0 20px 0; line-height: 1.5;"></p>
                <div style="display: flex; justify-content: center; gap: 12px;">
                    <button id="ai-dialog-cancel" style="padding: 7px 18px; background: #27272a; color: #a1a1aa; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;">再检查一下</button>
                    <button id="ai-dialog-ok" style="padding: 7px 18px; background: #22c55e; color: #09090b; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px;">确认并全自动重构</button>
                </div>
            </div>
        `;
        document.body.appendChild(confirmModal);

        const toast = document.createElement('div');
        toast.id = 'ai-toast-msg';
        toast.style.cssText = 'position: fixed; top: 24px; left: 50%; transform: translateX(-50%) translateY(-100px); background: #22c55e; color: #09090b; padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 13px; z-index: 2147483647; box-shadow: 0 10px 25px rgba(34,197,94,0.3); transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); font-family: -apple-system, BlinkMacSystemFont, sans-serif; pointer-events: none;';
        document.body.appendChild(toast);

        return true;
    }

    const checkTimer = setInterval(() => {
        if (injectElements()) {
            clearInterval(checkTimer);
            setupListeners();
        }
    }, 50);

    function setupListeners() {
        const highlightBox = document.getElementById('ai-highlight-box');
        const modalBox = document.getElementById('ai-modal-box');
        const targetInfo = document.getElementById('ai-target-info');
        const noteInput = document.getElementById('ai-note-input');
        const cancelBtn = document.getElementById('ai-cancel-btn');
        const submitBtn = document.getElementById('ai-submit-btn');
        const batchPanelDiv = document.getElementById('ai-batch-panel');
        const listContainer = document.getElementById('ai-list-container');
        const countSpan = document.getElementById('ai-count');
        const exportBtn = document.getElementById('ai-export-btn');

        const confirmBox = document.getElementById('ai-confirm-modal');
        const confirmText = document.getElementById('ai-confirm-text');
        const dialogCancel = document.getElementById('ai-dialog-cancel');
        const dialogOk = document.getElementById('ai-dialog-ok');
        const toast = document.getElementById('ai-toast-msg');

        function showToast(msg) {
            toast.innerText = msg;
            toast.style.transform = 'translateX(-50%) translateY(0)';
            setTimeout(() => { toast.style.transform = 'translateX(-50%) translateY(-100px)'; }, 3000);
        }

        let pendingEl = null;

        document.addEventListener('mousemove', function(e) {
            if (!e.shiftKey) {
                if (highlightBox && highlightBox.style.display !== 'none') highlightBox.style.display = 'none';
                return;
            }
            if (e.target.closest('#ai-batch-panel') || e.target.closest('#ai-modal-box') || e.target.closest('#ai-confirm-modal')) {
                if (highlightBox) highlightBox.style.display = 'none';
                return;
            }

            const target = e.target;
            const rect = target.getBoundingClientRect();

            if (highlightBox) {
                highlightBox.style.display = 'block';
                highlightBox.style.top = (rect.top - 2) + 'px';
                highlightBox.style.left = (rect.left - 2) + 'px';
                highlightBox.style.width = (rect.width + 4) + 'px';
                highlightBox.style.height = (rect.height + 4) + 'px';
            }
        }, true);

        window.addEventListener('keyup', (e) => {
            if (e.key === 'Shift' && highlightBox) highlightBox.style.display = 'none';
        });

        document.addEventListener('click', function(e) {
            if (!e.shiftKey) return;
            if (e.target.closest('#ai-batch-panel') || e.target.closest('#ai-modal-box') || e.target.closest('#ai-confirm-modal')) return;

            e.preventDefault();
            e.stopPropagation();

            if (highlightBox) highlightBox.style.display = 'none';
            pendingEl = e.target;

            const tag = pendingEl.tagName.toLowerCase();
            const className = pendingEl.className;

            let boundEvents = [];
            for (let attr of pendingEl.attributes) {
                if (attr.name.startsWith('@') || attr.name.startsWith('v-on:') || attr.name === 'onclick') {
                    boundEvents.push(`${attr.name}="${attr.value}"`);
                }
            }

            const displayVal = pendingEl.value || pendingEl.innerText || pendingEl.placeholder || '';
            const text = displayVal ? displayVal.substring(0, 35).trim() : '';

            targetInfo.innerHTML = `目标: <b>&lt;${tag}&gt;</b> | 类名: <code>${className || '无'}</code><br>` +
                                   `绑定的交互事件: <code style="color: #22c55e;">${boundEvents.length ? boundEvents.join(' ') : '无显式事件属性'}</code><br>` +
                                   `内容摘要: <i>"${text}"</i>`;
            noteInput.value = '';
            modalBox.style.display = 'flex';
            noteInput.focus();
        }, true);

        cancelBtn.addEventListener('click', () => {
            modalBox.style.display = 'none';
            pendingEl = null;
        });

        submitBtn.addEventListener('click', () => {
            const note = noteInput.value.trim();
            if (!note || !pendingEl) return;

            let ancestors = [];
            let parent = pendingEl.parentElement;
            let depth = 0;
            while (parent && depth < 5) {
                let info = parent.tagName.toLowerCase();
                if (parent.id) info += `#${parent.id}`;
                if (parent.className && typeof parent.className === 'string') {
                    info += `.${parent.className.trim().split(/\\s+/).join('.')}`;
                }
                ancestors.push(info);
                parent = parent.parentElement;
                depth++;
            }

            let boundEvents = [];
            for (let attr of pendingEl.attributes) {
                if (attr.name.startsWith('@') || attr.name.startsWith('v-on:') || attr.name === 'onclick') {
                    boundEvents.push(`${attr.name}="${attr.value}"`);
                }
            }

            const index = window.__ai_annotations.length + 1;
            const rect = pendingEl.getBoundingClientRect();

            const badge = document.createElement('div');
            badge.className = 'ai-badge-marker';
            badge.innerText = index;
            badge.style.cssText = `position: fixed; top: ${rect.top - 8}px; left: ${rect.right - 8}px; background: #ef4444; color: #fff; font-size: 10px; font-weight: 700; width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 2147483647; pointer-events: none; box-shadow: 0 2px 6px rgba(239,68,68,0.4); font-family: sans-serif;`;
            document.body.appendChild(badge);

            const elText = pendingEl.value || pendingEl.innerText || pendingEl.placeholder || '';
            const computedStyle = window.getComputedStyle(pendingEl);
            const stylesSummary = `color: ${computedStyle.color}, fontSize: ${computedStyle.fontSize}`;

            const payload = {
                id: index,
                tag: pendingEl.tagName.toLowerCase(),
                className: pendingEl.className,
                events: boundEvents,
                text: elText ? elText.substring(0, 60).trim() : '',
                siblingText: getNearbyText(pendingEl),
                ancestors: ancestors.reverse(),
                xpath: getXpath(pendingEl),
                styles: stylesSummary,
                note: note
            };

            window.__ai_annotations.push(payload);

            batchPanelDiv.style.display = 'block';
            countSpan.innerText = window.__ai_annotations.length;

            const item = document.createElement('div');
            item.style.cssText = 'background: #09090b; padding: 8px 10px; border-radius: 6px; border-left: 3px solid #22c55e; border: 1px solid #27272a;';
            item.innerHTML = `<div style="color: #22c55e; font-weight: 600; margin-bottom: 2px;">#${index} &lt;${payload.tag}&gt;</div><div style="color: #a1a1aa; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${note}</div>`;
            listContainer.appendChild(item);

            modalBox.style.display = 'none';
            pendingEl = null;

            showToast(`✅ 成功添加第 ${index} 个深度逻辑任务！`);
        });

        exportBtn.addEventListener('click', () => {
            if (window.__ai_annotations.length === 0) {
                showToast("⚠️ 还没有添加任务！");
                return;
            }
            confirmText.innerText = `当前已收集 ${window.__ai_annotations.length} 个深度逻辑/交互批注。确认开始全自动重构吗？`;
            confirmBox.style.display = 'flex';
        });

        dialogCancel.addEventListener('click', () => { confirmBox.style.display = 'none'; });

        dialogOk.addEventListener('click', () => {
            confirmBox.style.display = 'none';
            console.log("AI_BATCH_DATA:" + JSON.stringify(window.__ai_annotations));
            window.__ai_annotations = [];
            listContainer.innerHTML = '';
            countSpan.innerText = '0';
            batchPanelDiv.style.display = 'none';
            document.querySelectorAll('.ai-badge-marker').forEach(el => el.remove());
            showToast("🚀 任务已提交，终端正在深度重构业务逻辑...");
        });
    }

    function getNearbyText(el) {
        try {
            let parent = el.parentElement;
            if (!parent) return '';
            return parent.innerText.substring(0, 150).replace(/\\n/g, ' ');
        } catch(e) { return ''; }
    }

    function getXpath(element) {
        if (element.id !== '') return 'id("' + element.id + '")';
        if (element === document.body) return element.tagName;
        let ix = 0;
        let siblings = element.parentNode.childNodes;
        for (let i = 0; i < siblings.length; i++) {
            let sibling = siblings[i];
            if (sibling === element) return getXpath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;
        }
    }
})();
"""

async def main():
    os.chdir(PROJECT_ROOT)
    print(f"📂 当前项目根目录: {PROJECT_ROOT}")

    try:
        async with async_playwright() as p:
            print("🚀 正在启动浏览器...")
            try:
                browser = await p.chromium.launch(headless=False)
            except Exception as e:
                print(f"\n❌ [错误] 启动浏览器失败: {e}\n")
                return

            context = await browser.new_context(viewport={"width": 1280, "height": 800})
            await context.add_init_script(INJECTION_SCRIPT)

            page = await context.new_page()
            page.on("console", lambda msg: handle_browser_console(msg))

            target_url = "http://localhost:8888"
            print(f"正在打开页面: {target_url} ...")

            try:
                await page.goto(target_url, timeout=10000)
            except Exception as e:
                print(f"\n❌ [错误] 无法打开网页 {target_url}: {e}\n")
                await browser.close()
                return

            print("✨ 脚本运行中！请在浏览器中按住 Shift 点击需要修改【逻辑/交互】的元素...")
            print("按 Ctrl+C 随时退出程序。\n")

            try:
                await asyncio.Future()
            except KeyboardInterrupt:
                pass

    except Exception as e:
        print(f"\n❌ [严重错误] {e}\n")

def handle_browser_console(msg):
    text = msg.text
    if text.startswith("AI_BATCH_DATA:"):
        raw_json = text.replace("AI_BATCH_DATA:", "")
        items = json.loads(raw_json)
        asyncio.create_task(process_batch_tasks(items))
    else:
        print(f"🖥️ [Browser Console] {text}")

async def process_batch_tasks(items):
    total_items = len(items)
    print("\n" + "="*70)
    print(f"🎯 成功收集 {total_items} 个逻辑重构任务，开始深度全自动处理...")
    print("="*70)

    context_file_path = os.path.join(PROJECT_ROOT, "task_context.md")

    for idx, item in enumerate(items, 1):
        print("\n" + "~"*70)
        print(f"🔄 正在调用 AI 处理第 [{idx}/{total_items}] 项任务 (ID: #{item['id']})")
        print(f"📌 逻辑需求: {item['note']}")
        print(f"🎯 目标标签: <{item['tag']}> | 绑定事件: {item['events'] or '无'} | 文本: {item['text']}")
        print("~"*70 + "\n")

        with open(context_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Deep Logic Refactoring Task for Claude Code\n\n")
            f.write(f"You are refactoring business logic for **Task #{item['id']}** (Item {idx} of total {total_items}).\n\n")
            f.write(f"## 📋 Modification Requirement (Logic & Interaction)\n")
            f.write(f"- **Goal / Requirement**: `{item['note']}`\n")
            f.write(f"- **Target Element Tag**: `<{item['tag']}>`\n")
            f.write(f"- **Bound Events on DOM**: `{', '.join(item['events']) if item['events'] else 'None'}`\n")
            f.write(f"- **Unique Text / Value**: `{item['text']}`\n")
            f.write(f"- **DOM Ancestor Chain**: `{' > '.join(item['ancestors'])}`\n")
            f.write(f"- **Surrounding Context**: *\"{item['siblingText']}\"*\n\n")
            f.write(f"## 🛠️ CRITICAL INSTRUCTIONS FOR LOGIC REFACTORING:\n")
            f.write(f"1. **Trace the Handler Function**: Look at the bound event attributes (like `@click`, `v-on`, etc.) on the element or search for its parent component to find the exact JavaScript/TypeScript function name being called (e.g., `handleSubmit`, `validateForm`).\n")
            f.write(f"2. **Bypass or Rewrite Logic**: If the requirement says to remove validation, bypass checks, or mock a successful response:\n")
            f.write(f"   - Open the component file (`.vue` or `.tsx` / `.js`).\n")
            f.write(f"   - Locate the function/method implementation.\n")
            f.write(f"   - Directly comment out or remove the validation statements (e.g., `formRef.value.validate()`, `if (!account) return`).\n")
            f.write(f"   - Inject direct success handling or mock successful execution so the UI behaves as requested without blocking.\n")
            f.write(f"3. **Do Not Hesitate**: Modify the files directly and thoroughly. Do not ask for confirmation.")

        prompt_arg = (
            f"Please read task_context.md. This is a DEEP LOGIC REFACTORING task for Task #{item['id']}: '{item['note']}'. "
            f"Find the source file, trace the click/event handler function, remove validation or alter the logic as requested, "
            f"and implement it directly. CRITICAL: Modify the code files now without asking questions."
        )

        try:
            success = await run_claude_with_live_stream(prompt_arg, item['id'], idx, total_items)
            if success:
                print(f"\n✅ [进度汇报] 第 [{idx}/{total_items}] 项逻辑任务 (ID: #{item['id']}) 重构完成！\n")
            else:
                print(f"\n❌ [错误] 逻辑任务 #{item['id']} 执行失败。\n")
        except Exception as e:
            print(f"\n❌ [错误] 逻辑任务 #{item['id']} 出错：{e}\n")

    print("="*70)
    print(f"✨ 全部 {total_items} 个逻辑任务已重构完毕！")
    print("="*70 + "\n")

async def run_claude_with_live_stream(prompt_arg, task_id, current_idx, total_items):
    env = os.environ.copy()
    env["FORCE_COLOR"] = "1"

    process = await asyncio.create_subprocess_exec(
        'claude', '--dangerously-skip-permissions', '-p', prompt_arg,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=PROJECT_ROOT,
        env=env
    )

    if process.stdin:
        process.stdin.close()

    output_lines = []

    async def read_stream(stream):
        while True:
            line = await stream.readline()
            if not line: break
            decoded = line.decode('utf-8', errors='ignore').strip()
            if decoded:
                output_lines.append(decoded)

    stdout_task = asyncio.create_task(read_stream(process.stdout))
    stderr_task = asyncio.create_task(read_stream(process.stderr))

    spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start_time = asyncio.get_event_loop().time()
    spinner_idx = 0
    last_printed_count = 0

    while process.returncode is None:
        try:
            await asyncio.wait_for(process.wait(), timeout=0.1)
            break
        except asyncio.TimeoutError:
            pass

        # 实时打印后台真实吐出的进度/状态日志
        while last_printed_count < len(output_lines):
            sys.stdout.write("\r\033[K")
            print(f"  ⚡ {output_lines[last_printed_count]}")
            last_printed_count += 1

        elapsed = int(asyncio.get_event_loop().time() - start_time)
        spinner = spinners[spinner_idx % len(spinners)]
        spinner_idx += 1

        # 动态活动状态栏（带耗时和活跃动效，绝不单调）
        sys.stdout.write(
            f"\r{spinner} 🧠 [AI 运行中] 正在重构任务 [{current_idx}/{total_items}] (ID: #{task_id}) "
            f"| 已耗时: {elapsed}s | 正在进行推理与代码读写...    "
        )
        sys.stdout.flush()

    await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

    sys.stdout.write("\r" + " " * 120 + "\r")
    sys.stdout.flush()

    total_elapsed = int(asyncio.get_event_loop().time() - start_time)
    if process.returncode == 0:
        print(f"✨ 逻辑任务 #{task_id} 重构成功！(耗时: {total_elapsed} 秒)")
        return True
    else:
        print(f"❌ 逻辑任务 #{task_id} 执行出错 (耗时: {total_elapsed} 秒)")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已手动终止。")
