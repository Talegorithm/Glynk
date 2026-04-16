# Bug: 删除高亮后同位置无法再次弹出选区工具栏

## 复现步骤

1. 在阅读器中划选一段文字，弹出 SelectionToolbar
2. 点击高亮（任意颜色），创建成功
3. 右键点击高亮 → 删除
4. 在**同一位置**再次划选文字
5. **预期**：弹出 SelectionToolbar
6. **实际**：不弹出。但在其他未被高亮过的位置划选仍然正常

## 已确认的代码问题

`glynk-web/src/utils/reader/selection.ts` 第 335-362 行 `removeHighlightById()`：

```js
// 第 342-345 行
if (htmlElement.hasAttribute('data-highlighted') && htmlElement.parentElement?.id) {
  const textNode = document.createTextNode(htmlElement.textContent || '');
  htmlElement.parentNode?.replaceChild(textNode, htmlElement);
  htmlElement.parentElement?.normalize();  // ← BUG: htmlElement 已脱离 DOM，parentElement 为 null
}
```

`replaceChild` 执行后 `htmlElement` 不再在 DOM 树中，`htmlElement.parentElement` 为 `null`，`normalize()` 永远不会执行。

### 后果

原本 `<span id="xxx">完整文本</span>` 被高亮时拆成：
```html
<span id="xxx">"前文"[text] + <span data-highlighted>"高亮"</span> + "后文"[text]</span>
```

删除高亮后应合并回一个文本节点，但因为 `normalize()` 没执行，变成：
```html
<span id="xxx">"前文"[text] + "高亮"[text] + "后文"[text]</span>
```

三个碎片化的文本节点没有合并。

### 修复方向

```js
const parent = htmlElement.parentNode;
const textNode = document.createTextNode(htmlElement.textContent || '');
parent?.replaceChild(textNode, htmlElement);
(parent as HTMLElement)?.normalize();
```

先保存 `parentNode` 引用，替换后在保存的引用上调用 `normalize()`。

## 待排查

文本节点碎片化是否是 SelectionToolbar 不弹出的**唯一原因**，还需确认：

1. `collectSpansInRange()` 在碎片化 DOM 下是否仍能正确找到 span — 从代码逻辑看理论上有 fallback 到 `.reader-content`，应该能找到
2. ReaderContent.tsx 的 `mouseup` / `selectionchange` 事件处理是否有状态问题（如 `selectionRange` 被错误置空）
3. 高亮删除后 React 状态（`annotations` 数组）更新是否触发了非预期的 re-render，影响了事件监听

如果修复 `normalize()` 后问题依然存在，需要在 ReaderContent.tsx 的选区处理逻辑中加断点排查。
