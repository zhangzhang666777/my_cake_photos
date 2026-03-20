import os
import json

# ========== 配置部分 ==========
PHOTO_ROOT = "D:/my_cake_photos"      # 照片根目录
OUTPUT_FILE = "index.html"            # 输出的HTML文件名
TITLE = "华味嘉蛋糕电子相册"          # 网页标题

# 支持的图片格式
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

# 缩略图配置
ENABLE_THUMBNAIL = True                # 是否生成缩略图
THUMB_SIZE = (120, 120)                # 缩略图尺寸（手机端可更小）
THUMB_QUALITY = 70                      # WebP 质量 (1-100)，70 平衡体积与画质
THUMB_ROOT = os.path.join(PHOTO_ROOT, '__thumbs__')  # 缩略图存储目录

# 分页配置
PAGE_SIZE = 10                          # 每页加载图片数量（移动端减少并发）
# ==============================

# 尝试导入Pillow
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    if ENABLE_THUMBNAIL:
        print("⚠️ 未安装Pillow库，缩略图功能将禁用。请运行: pip install Pillow")
        ENABLE_THUMBNAIL = False

def generate_thumbnail(src_path, thumb_path):
    """
    生成 WebP 缩略图。
    thumb_path 是带原扩展名的路径（如 __thumbs__/a/b/c.jpg），
    函数内部自动转换为同目录下的 .webp 文件名。
    """
    try:
        # 构造 WebP 路径：取目录 + 文件名（无扩展名） + .webp
        base_name = os.path.splitext(os.path.basename(thumb_path))[0]
        thumb_dir = os.path.dirname(thumb_path)
        webp_path = os.path.join(thumb_dir, base_name + '.webp')
        os.makedirs(thumb_dir, exist_ok=True)

        with Image.open(src_path) as img:
            # 转换为RGB（处理PNG透明背景）
            if img.mode in ('RGBA', 'LA', 'P'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 生成缩略图（保持比例）
            img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)

            # 如果尺寸不足，创建白色画布并居中粘贴
            if img.size != THUMB_SIZE:
                new_img = Image.new('RGB', THUMB_SIZE, (255, 255, 255))
                offset = ((THUMB_SIZE[0] - img.size[0]) // 2,
                          (THUMB_SIZE[1] - img.size[1]) // 2)
                new_img.paste(img, offset)
                new_img.save(webp_path, 'WEBP', quality=THUMB_QUALITY, method=6)
            else:
                img.save(webp_path, 'WEBP', quality=THUMB_QUALITY, method=6)

        return True
    except Exception as e:
        print(f"  缩略图生成失败: {src_path} -> {e}")
        return False

def build_tree(current_path, rel_path=""):
    """递归构建分类树（跳过 __thumbs__ 文件夹）"""
    nodes = []
    try:
        items = os.listdir(current_path)
    except PermissionError:
        return nodes

    for item in sorted(items):
        if item == '__thumbs__' or item.startswith('.'):
            continue
        item_path = os.path.join(current_path, item)
        if os.path.isdir(item_path):
            child_rel = os.path.join(rel_path, item) if rel_path else item
            children = build_tree(item_path, child_rel)

            # 收集当前目录的图片
            images = []
            for file in os.listdir(item_path):
                file_path = os.path.join(item_path, file)
                if os.path.isfile(file_path) and file.lower().endswith(IMAGE_EXTENSIONS):
                    # 生成缩略图
                    if ENABLE_THUMBNAIL and HAS_PIL:
                        thumb_rel_path = rel_path.replace('\\', '/')
                        thumb_dir = os.path.join(THUMB_ROOT, *thumb_rel_path.split('/')) if thumb_rel_path else THUMB_ROOT
                        thumb_path = os.path.join(thumb_dir, file)
                        if not os.path.exists(thumb_path) or os.path.getmtime(file_path) > os.path.getmtime(thumb_path):
                            generate_thumbnail(file_path, thumb_path)
                    images.append(file)
            images.sort()

            node = {
                "name": item,
                "rel_path": child_rel.replace('\\', '/'),
                "images": images,
                "children": children
            }
            if images or children:
                nodes.append(node)
    return nodes

print("🔍 正在扫描目录并生成 WebP 缩略图（首次可能较慢）...")
tree = build_tree(PHOTO_ROOT)
if not tree:
    print("❌ 未找到任何图片分类，请检查根目录下是否有包含图片的子文件夹。")
    exit()

tree_json = json.dumps(tree, ensure_ascii=False)

# ==================== 生成HTML ====================
html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{TITLE}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f4f7fb; }}
        #container {{ display: flex; min-height: 100vh; }}

        /* 左侧导航 - 清爽风格，无箭头 */
        #sidebar {{
            width: 280px; background-color: #ffffff; color: #2c3e50; padding: 24px 16px;
            box-shadow: 2px 0 12px rgba(0,0,0,0.03); overflow-y: auto; height: 100vh;
            position: sticky; top: 0; border-right: 1px solid #e9ecef;
        }}
        #sidebar h2 {{ font-size: 1.3rem; font-weight: 600; margin-bottom: 24px; color: #1e2a3a; padding-bottom: 12px; border-bottom: 2px solid #e9ecef; }}
        .tree, .tree ul {{ list-style: none; margin: 0; padding-left: 0; }}
        .tree li {{ margin: 2px 0; line-height: 1.5; }}
        .tree .node-row {{ display: flex; align-items: center; padding: 6px 8px; border-radius: 8px; transition: background-color 0.15s; cursor: default; }}
        .tree .node-row:hover {{ background-color: #f1f5f9; }}
        .tree .icon {{ width: 28px; text-align: left; color: #5f6b7a; font-size: 1rem; cursor: pointer; transition: color 0.15s; }}
        .tree .icon:hover {{ color: #0d6efd; }}
        .tree .name {{ flex: 1; font-size: 0.95rem; color: #2c3e50; padding: 2px 6px; border-radius: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; justify-content: space-between; }}
        .tree .name.clickable {{ cursor: pointer; }}
        .tree .name.clickable:hover {{ background-color: #e1e8f0; }}
        .tree .name.active {{ background-color: #0d6efd; color: white; font-weight: 500; }}
        .tree .badge {{ background-color: #e9ecef; color: #495057; font-size: 0.7rem; font-weight: 500; padding: 2px 8px; border-radius: 30px; margin-left: 8px; }}
        .tree .name.active .badge {{ background-color: rgba(255,255,255,0.25); color: white; }}
        .tree .folder-content {{ margin-left: 28px; display: block; }}
        .tree .folder-content.collapsed {{ display: none; }}

        /* 右侧主内容区 */
        #main {{ flex: 1; padding: 24px; display: flex; flex-direction: column; }}
        #top-showcase {{ background: white; border-radius: 16px; padding: 20px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.02); border: 1px solid #edf2f7; }}
        #showcase-title {{ font-size: 1.1rem; font-weight: 600; color: #1e293b; margin-bottom: 16px; }}
        #showcase-images {{ display: flex; justify-content: space-around; align-items: center; gap: 20px; }}
        .showcase-item {{ text-align: center; flex: 1; }}
        .showcase-item img {{ width: 100%; max-width: 200px; height: 150px; object-fit: cover; border-radius: 12px; box-shadow: 0 6px 14px rgba(0,0,0,0.06); }}
        .showcase-item p {{ margin-top: 8px; font-size: 0.85rem; color: #4b5563; }}
        #showcase-controls {{ display: flex; justify-content: center; margin-top: 16px; gap: 12px; }}
        #showcase-controls button {{ background: white; border: 1px solid #d1d9e6; color: #1e293b; padding: 8px 22px; border-radius: 40px; cursor: pointer; font-size: 0.95rem; font-weight: 500; transition: all 0.15s; }}
        #showcase-controls button:hover {{ background: #f1f5f9; border-color: #a0b3cc; }}
        #showcase-controls button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
        #gallery {{ background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.02); border: 1px solid #edf2f7; flex: 1; }}
        .gallery-grid {{ display: flex; flex-wrap: wrap; gap: 16px; justify-content: center; }}
        .gallery-grid img {{ width: 120px; height: 120px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.04); cursor: pointer; transition: transform 0.15s; background-color: #f8fafc; border: 1px solid #eef2f6; }}
        .gallery-grid img:hover {{ transform: scale(1.02); }}
        .no-images {{ text-align: center; color: #94a3b8; padding: 60px; font-size: 1rem; }}

        /* 预览悬浮窗（带文件名，无后缀） */
        #preview-container {{
            display: none; position: fixed; bottom: 30px; right: 30px; background: white;
            border-radius: 16px; padding: 12px 12px 8px; box-shadow: 0 20px 30px rgba(0,0,0,0.2);
            border: 1px solid #e9eef3; z-index: 1000; max-width: 80vw; max-height: 80vh; text-align: center;
        }}
        #preview-img {{ display: block; max-width: 100%; max-height: 65vh; object-fit: contain; border-radius: 8px; }}
        .preview-filename {{ margin-top: 8px; padding: 6px 12px; background: rgba(0,0,0,0.6); color: white; font-size: 0.9rem; border-radius: 30px; display: inline-block; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.2); }}

        /* 加载更多指示器及底部哨兵 */
        .loading-more {{
            text-align: center; padding: 20px; color: #94a3b8; width: 100%;
        }}
        #sentinel {{
            height: 10px;
            width: 100%;
            visibility: hidden;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="sidebar">
            <h2>📁 相册分类</h2>
            <ul class="tree" id="category-tree"></ul>
        </div>
        <div id="main">
            <div id="top-showcase">
                <div id="showcase-title">✨ 精选展示</div>
                <div id="showcase-images"></div>
                <div id="showcase-controls">
                    <button id="prev-showcase" onclick="prevShowcase()">← 上一组</button>
                    <button id="next-showcase" onclick="nextShowcase()">下一组 →</button>
                </div>
            </div>
            <div id="gallery">
                <div id="gallery-grid" class="gallery-grid"></div>
                <div id="sentinel"></div> <!-- 用于触发加载的哨兵元素 -->
                <div id="loading-more" class="loading-more" style="display: none;">加载中...</div>
            </div>
        </div>
    </div>

    <div id="preview-container">
        <img id="preview-img" src="" alt="预览">
        <div id="preview-filename" class="preview-filename"></div>
    </div>

    <script>
        const treeData = {tree_json};
        const ENABLE_THUMBNAIL = {str(ENABLE_THUMBNAIL).lower()};
        const PAGE_SIZE = {PAGE_SIZE};  // 每页加载数量

        let currentNode = null;
        let currentImages = [];
        let showcaseStartIndex = 0;
        let loadedCount = 0;          // 当前已加载的图片数量
        let isLoading = false;         // 防止重复加载
        let hasMore = true;            // 是否还有更多图片

        const treeEl = document.getElementById('category-tree');
        const showcaseImagesEl = document.getElementById('showcase-images');
        const galleryGridEl = document.getElementById('gallery-grid');
        const sentinelEl = document.getElementById('sentinel');
        const loadingMoreEl = document.getElementById('loading-more');
        const prevBtn = document.getElementById('prev-showcase');
        const nextBtn = document.getElementById('next-showcase');
        const previewContainer = document.getElementById('preview-container');
        const previewImg = document.getElementById('preview-img');
        const previewFilename = document.getElementById('preview-filename');

        // 辅助函数：去除文件名后缀
        function removeExtension(filename) {{
            return filename.replace(/\\.[^/.]+$/, '');
        }}

        // 懒加载观察器
        const lazyObserver = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const img = entry.target;
                    const dataSrc = img.getAttribute('data-src');
                    if (dataSrc && !img.src) {{
                        img.src = dataSrc;
                        img.removeAttribute('data-src');
                    }}
                }}
            }});
        }}, {{ rootMargin: '100px', threshold: 0.01 }});

        function observeLazyImages() {{
            document.querySelectorAll('#gallery-grid img[data-src]').forEach(img => lazyObserver.observe(img));
        }}

        // ---------- 无限滚动 IntersectionObserver ----------
        let sentinelObserver = null;

        function initInfiniteScroll() {{
            if (sentinelObserver) {{
                sentinelObserver.disconnect();
            }}
            sentinelObserver = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting && !isLoading && hasMore) {{
                        loadMoreImages();
                    }}
                }});
            }}, {{
                rootMargin: '100px', // 提前100px触发，提升流畅度
                threshold: 0.01
            }});
            sentinelObserver.observe(sentinelEl);
        }}

        // 销毁观察器（切换文件夹时重新绑定）
        function resetInfiniteScroll() {{
            if (sentinelObserver) {{
                sentinelObserver.disconnect();
            }}
            initInfiniteScroll();
        }}

        function loadMoreImages() {{
            if (isLoading || !hasMore || !currentImages) return;
            isLoading = true;
            loadingMoreEl.style.display = 'block';

            setTimeout(() => {{
                const start = loadedCount;
                const end = Math.min(loadedCount + PAGE_SIZE, currentImages.length);
                for (let i = start; i < end; i++) {{
                    const imgName = currentImages[i];
                    addImageToGrid(imgName);
                }}
                loadedCount = end;
                hasMore = loadedCount < currentImages.length;
                isLoading = false;
                loadingMoreEl.style.display = hasMore ? 'block' : 'none';
                observeLazyImages();
            }}, 10);
        }}

        function addImageToGrid(imgName) {{
            const folder = currentNode.rel_path;
            const fullPath = `${{folder}}/${{imgName}}`;
            let thumbPath = fullPath;
            if (ENABLE_THUMBNAIL) {{
                const baseName = removeExtension(imgName);          // 无后缀文件名
                thumbPath = `__thumbs__/${{folder}}/${{baseName}}.webp`; // WebP 缩略图路径
            }}

            const img = document.createElement('img');
            img.setAttribute('data-src', thumbPath);
            img.setAttribute('data-fullsrc', fullPath);
            img.alt = removeExtension(imgName);  // 用于预览显示

            img.onerror = function() {{
                // 如果缩略图加载失败（如不存在或格式不支持），尝试原图
                if (this.src !== this.getAttribute('data-fullsrc')) {{
                    this.src = this.getAttribute('data-fullsrc');
                    this.onerror = null;
                }}
            }};

            img.addEventListener('mouseenter', () => {{
                previewImg.src = fullPath;
                previewFilename.textContent = removeExtension(imgName);
                previewContainer.style.display = 'block';
            }});
            img.addEventListener('mouseleave', () => {{
                previewContainer.style.display = 'none';
            }});

            galleryGridEl.appendChild(img);
        }}

        // 重置分页（切换文件夹时调用）
        function resetGallery() {{
            galleryGridEl.innerHTML = '';
            loadedCount = 0;
            hasMore = currentImages.length > 0;
            isLoading = false;
            loadingMoreEl.style.display = 'block';
            // 重置哨兵观察器
            resetInfiniteScroll();
            setTimeout(() => {{
                const end = Math.min(PAGE_SIZE, currentImages.length);
                for (let i = 0; i < end; i++) {{
                    addImageToGrid(currentImages[i]);
                }}
                loadedCount = end;
                hasMore = loadedCount < currentImages.length;
                loadingMoreEl.style.display = hasMore ? 'block' : 'none';
                observeLazyImages();
            }}, 10);
        }}

        // 渲染树（无箭头，双击文件夹折叠/展开）
        function renderTree(nodes, parentElement) {{
            nodes.forEach(node => {{
                const li = document.createElement('li');
                li.dataset.path = node.rel_path;

                const hasChildren = node.children && node.children.length > 0;
                const hasImages = node.images && node.images.length > 0;

                const rowDiv = document.createElement('div');
                rowDiv.className = 'node-row';

                // 图标区域
                const iconSpan = document.createElement('span');
                iconSpan.className = 'icon';
                if (hasChildren) {{
                    iconSpan.innerHTML = '<i class="fas fa-folder"></i>';
                }} else {{
                    iconSpan.innerHTML = '<i class="fas fa-image"></i>';
                }}
                rowDiv.appendChild(iconSpan);

                // 名称区域
                const nameSpan = document.createElement('span');
                nameSpan.className = 'name' + (hasImages ? ' clickable' : '');
                nameSpan.textContent = node.name;
                if (hasImages) {{
                    const badge = document.createElement('span');
                    badge.className = 'badge';
                    badge.textContent = node.images.length;
                    nameSpan.appendChild(badge);
                }}

                // 单击名称切换图片（仅当有图片时）
                if (hasImages) {{
                    nameSpan.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        document.querySelectorAll('.tree .name.active').forEach(el => el.classList.remove('active'));
                        nameSpan.classList.add('active');
                        switchNode(node);
                    }});
                }}

                rowDiv.appendChild(nameSpan);
                li.appendChild(rowDiv);

                // 子文件夹容器
                if (hasChildren) {{
                    const childUl = document.createElement('ul');
                    childUl.className = 'folder-content';
                    li.appendChild(childUl);
                    renderTree(node.children, childUl);
                }}

                // 双击文件夹折叠/展开
                if (hasChildren) {{
                    li.addEventListener('dblclick', (e) => {{
                        e.stopPropagation();
                        const content = li.querySelector('.folder-content');
                        if (content) {{
                            content.classList.toggle('collapsed');
                        }}
                    }});
                }}

                parentElement.appendChild(li);
            }});
        }}

        function switchNode(node) {{
            currentNode = node;
            currentImages = node.images || [];
            showcaseStartIndex = 0;
            updateShowcase();
            resetGallery();
        }}

        function updateShowcase() {{
            const images = currentImages;
            const total = images.length;
            showcaseImagesEl.innerHTML = '';

            if (total === 0) {{
                showcaseImagesEl.innerHTML = '<div class="no-images">暂无图片</div>';
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                return;
            }}

            let indices = [];
            for (let i = 0; i < 3; i++) {{
                let idx = (showcaseStartIndex + i) % total;
                indices.push(idx);
            }}

            indices.forEach(idx => {{
                const imgName = images[idx];
                const imgPath = `${{currentNode.rel_path}}/${{imgName}}`;
                const displayName = removeExtension(imgName);
                const div = document.createElement('div');
                div.className = 'showcase-item';
                div.innerHTML = `<img src="${{imgPath}}" alt="${{displayName}}" loading="lazy" onerror="this.src='${{imgPath}}'; this.onerror=null;"><p>${{displayName}}</p>`;
                showcaseImagesEl.appendChild(div);
            }});

            prevBtn.disabled = total <= 3;
            nextBtn.disabled = total <= 3;
        }}

        function prevShowcase() {{
            const total = currentImages.length;
            if (total <= 3) return;
            showcaseStartIndex = (showcaseStartIndex - 3 + total) % total;
            updateShowcase();
        }}

        function nextShowcase() {{
            const total = currentImages.length;
            if (total <= 3) return;
            showcaseStartIndex = (showcaseStartIndex + 3) % total;
            updateShowcase();
        }}

        // 初始化
        window.onload = function() {{
            renderTree(treeData, treeEl);
            initInfiniteScroll();  // 初始化哨兵观察器

            function findFirstWithImages(nodes) {{
                for (let node of nodes) {{
                    if (node.images && node.images.length > 0) return node;
                    if (node.children) {{
                        const found = findFirstWithImages(node.children);
                        if (found) return found;
                    }}
                }}
                return null;
            }}
            const firstNode = findFirstWithImages(treeData);
            if (firstNode) {{
                setTimeout(() => {{
                    switchNode(firstNode);
                    const allNames = document.querySelectorAll('.tree .name');
                    for (let nameSpan of allNames) {{
                        const li = nameSpan.closest('li');
                        if (li && li.dataset.path === firstNode.rel_path) {{
                            nameSpan.classList.add('active');
                            break;
                        }}
                    }}
                }}, 100);
            }}
        }};
    </script>
</body>
</html>
"""

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ 相册生成成功！文件名为：{OUTPUT_FILE}")
print(f"🖼️ 缩略图已转为 WebP 格式，质量 {THUMB_QUALITY}，尺寸 {THUMB_SIZE[0]}x{THUMB_SIZE[1]}")
print(f"📄 每页加载 {PAGE_SIZE} 张图片，滚动时自动加载更多（基于 IntersectionObserver）。")
print("📂 左侧导航自动隐藏 __thumbs__ 目录。")