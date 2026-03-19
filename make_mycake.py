import os
import json

# ========== 配置部分 ==========
PHOTO_ROOT = "D:/my_cake_photos"  # 照片根目录
OUTPUT_FILE = "index.html"  # 输出的HTML文件名
TITLE = "华味嘉蛋糕电子相册"  # 网页标题

# 支持的图片格式
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

# 缩略图配置
ENABLE_THUMBNAIL = True  # 是否生成缩略图（强烈建议开启）
THUMB_SIZE = (200, 200)  # 缩略图尺寸
THUMB_ROOT = os.path.join(PHOTO_ROOT, '__thumbs__')  # 缩略图存储目录
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
    """生成缩略图，成功返回True，失败返回False"""
    try:
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
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

            img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
            if img.size != THUMB_SIZE:
                new_img = Image.new('RGB', THUMB_SIZE, (255, 255, 255))
                offset = ((THUMB_SIZE[0] - img.size[0]) // 2,
                          (THUMB_SIZE[1] - img.size[1]) // 2)
                new_img.paste(img, offset)
                new_img.save(thumb_path, 'JPEG', quality=85)
            else:
                img.save(thumb_path, 'JPEG', quality=85)
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
        # 跳过缩略图目录和隐藏文件夹
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
                        thumb_dir = os.path.join(THUMB_ROOT,
                                                 *thumb_rel_path.split('/')) if thumb_rel_path else THUMB_ROOT
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


print("🔍 正在扫描目录并生成缩略图（首次可能较慢）...")
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
    <!-- Font Awesome 图标库 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f4f7fb; }}
        #container {{ display: flex; min-height: 100vh; }}

        /* ===== 左侧导航 ===== */
        #sidebar {{
            width: 280px;
            background-color: #ffffff;
            color: #2c3e50;
            padding: 24px 16px;
            box-shadow: 2px 0 12px rgba(0,0,0,0.03);
            overflow-y: auto;
            height: 100vh;
            position: sticky;
            top: 0;
            border-right: 1px solid #e9ecef;
        }}
        #sidebar h2 {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 24px;
            color: #1e2a3a;
            padding-bottom: 12px;
            border-bottom: 2px solid #e9ecef;
            letter-spacing: 0.3px;
        }}
        .tree, .tree ul {{
            list-style: none;
            margin: 0;
            padding-left: 0;
        }}
        .tree li {{
            margin: 2px 0;
            line-height: 1.5;
        }}
        .tree .node-row {{
            display: flex;
            align-items: center;
            padding: 6px 8px;
            border-radius: 8px;
            transition: background-color 0.15s;
            cursor: default;
        }}
        .tree .node-row:hover {{
            background-color: #f1f5f9;
        }}
        .tree .icon {{
            width: 28px;
            text-align: left;
            color: #5f6b7a;
            font-size: 1rem;
            cursor: pointer;
            transition: color 0.15s;
        }}
        .tree .icon:hover {{
            color: #0d6efd;
        }}
        .tree .name {{
            flex: 1;
            font-size: 0.95rem;
            color: #2c3e50;
            padding: 2px 6px;
            border-radius: 6px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .tree .name.clickable {{
            cursor: pointer;
        }}
        .tree .name.clickable:hover {{
            background-color: #e1e8f0;
        }}
        .tree .name.active {{
            background-color: #0d6efd;
            color: white;
            font-weight: 500;
        }}
        .tree .badge {{
            background-color: #e9ecef;
            color: #495057;
            font-size: 0.7rem;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 30px;
            margin-left: 8px;
            white-space: nowrap;
        }}
        .tree .name.active .badge {{
            background-color: rgba(255,255,255,0.25);
            color: white;
        }}
        .tree .folder-content {{
            margin-left: 28px;
            display: block;
        }}
        .tree .folder-content.collapsed {{
            display: none;
        }}

        /* ===== 右侧主内容区 ===== */
        #main {{
            flex: 1; padding: 24px; display: flex; flex-direction: column;
        }}
        #top-showcase {{
            background: white; border-radius: 16px; padding: 20px; margin-bottom: 24px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.02); border: 1px solid #edf2f7;
        }}
        #showcase-title {{ font-size: 1.1rem; font-weight: 600; color: #1e293b; margin-bottom: 16px; }}
        #showcase-images {{ display: flex; justify-content: space-around; align-items: center; gap: 20px; }}
        .showcase-item {{ text-align: center; flex: 1; }}
        .showcase-item img {{
            width: 100%; max-width: 200px; height: 150px; object-fit: cover;
            border-radius: 12px; box-shadow: 0 6px 14px rgba(0,0,0,0.06);
        }}
        .showcase-item p {{ margin-top: 8px; font-size: 0.85rem; color: #4b5563; }}
        #showcase-controls {{ display: flex; justify-content: center; margin-top: 16px; gap: 12px; }}
        #showcase-controls button {{
            background: white; border: 1px solid #d1d9e6; color: #1e293b;
            padding: 8px 22px; border-radius: 40px; cursor: pointer;
            font-size: 0.95rem; font-weight: 500; transition: all 0.15s;
        }}
        #showcase-controls button:hover {{
            background: #f1f5f9; border-color: #a0b3cc;
        }}
        #showcase-controls button:disabled {{
            opacity: 0.4; cursor: not-allowed;
        }}
        #gallery {{
            background: white; border-radius: 16px; padding: 24px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.02); border: 1px solid #edf2f7; flex: 1;
        }}
        .gallery-grid {{
            display: flex; flex-wrap: wrap; gap: 16px; justify-content: center;
        }}
        .gallery-grid img {{
            width: 200px; height: 200px; object-fit: cover; border-radius: 12px;
            box-shadow: 0 6px 14px rgba(0,0,0,0.04); cursor: pointer;
            transition: transform 0.15s, box-shadow 0.15s;
            background-color: #f8fafc; border: 1px solid #eef2f6;
        }}
        .gallery-grid img:hover {{
            transform: scale(1.02); box-shadow: 0 12px 24px rgba(0,0,0,0.08);
        }}
        .no-images {{ text-align: center; color: #94a3b8; padding: 60px; font-size: 1rem; }}

        /* ===== 预览悬浮窗（带文件名，无后缀） ===== */
        #preview-container {{
            display: none;
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: white;
            border-radius: 16px;
            padding: 12px 12px 8px 12px;
            box-shadow: 0 20px 30px rgba(0,0,0,0.2);
            border: 1px solid #e9eef3;
            z-index: 1000;
            max-width: 80vw;
            max-height: 80vh;
            text-align: center;
        }}
        #preview-img {{
            display: block;
            max-width: 100%;
            max-height: 65vh;
            object-fit: contain;
            border-radius: 8px;
        }}
        .preview-filename {{
            margin-top: 8px;
            padding: 6px 12px;
            background: rgba(0,0,0,0.6);
            color: white;
            font-size: 0.9rem;
            border-radius: 30px;
            display: inline-block;
            max-width: 100%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255,255,255,0.2);
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
            </div>
        </div>
    </div>

    <!-- 预览悬浮窗（含文件名显示，无后缀） -->
    <div id="preview-container">
        <img id="preview-img" src="" alt="预览">
        <div id="preview-filename" class="preview-filename"></div>
    </div>

    <script>
        const treeData = {tree_json};
        const ENABLE_THUMBNAIL = {str(ENABLE_THUMBNAIL).lower()};

        let currentNode = null;
        let currentImages = [];
        let showcaseStartIndex = 0;

        const treeEl = document.getElementById('category-tree');
        const showcaseImagesEl = document.getElementById('showcase-images');
        const galleryGridEl = document.getElementById('gallery-grid');
        const prevBtn = document.getElementById('prev-showcase');
        const nextBtn = document.getElementById('next-showcase');
        const previewContainer = document.getElementById('preview-container');
        const previewImg = document.getElementById('preview-img');
        const previewFilename = document.getElementById('preview-filename');

        // 辅助函数：去除文件名后缀
        function removeExtension(filename) {{
            return filename.replace(/\\.[^/.]+$/, '');
        }}

        // 懒加载
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
            document.querySelectorAll('img[data-src]').forEach(img => lazyObserver.observe(img));
        }}

        // 渲染树
        function renderTree(nodes, parentElement) {{
            nodes.forEach(node => {{
                const li = document.createElement('li');
                li.dataset.path = node.rel_path;

                const hasChildren = node.children && node.children.length > 0;
                const hasImages = node.images && node.images.length > 0;

                const rowDiv = document.createElement('div');
                rowDiv.className = 'node-row';

                const iconSpan = document.createElement('span');
                iconSpan.className = 'icon';
                if (hasChildren) {{
                    iconSpan.innerHTML = '<i class="fas fa-chevron-right"></i>';
                    iconSpan.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        const content = li.querySelector('.folder-content');
                        if (content) {{
                            content.classList.toggle('collapsed');
                            const i = iconSpan.querySelector('i');
                            if (content.classList.contains('collapsed')) {{
                                i.className = 'fas fa-chevron-right';
                            }} else {{
                                i.className = 'fas fa-chevron-down';
                            }}
                        }}
                    }});
                }} else {{
                    iconSpan.innerHTML = '<i class="fas fa-circle" style="font-size: 0.4rem; vertical-align: middle;"></i>';
                }}
                rowDiv.appendChild(iconSpan);

                const nameSpan = document.createElement('span');
                nameSpan.className = 'name' + (hasImages ? ' clickable' : '');
                nameSpan.textContent = node.name;
                if (hasImages) {{
                    const badge = document.createElement('span');
                    badge.className = 'badge';
                    badge.textContent = node.images.length;
                    nameSpan.appendChild(badge);
                }}

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

                if (hasChildren) {{
                    const childUl = document.createElement('ul');
                    childUl.className = 'folder-content';
                    li.appendChild(childUl);
                    renderTree(node.children, childUl);
                }}

                parentElement.appendChild(li);
            }});
        }}

        function switchNode(node) {{
            currentNode = node;
            currentImages = node.images || [];
            showcaseStartIndex = 0;
            updateShowcase();
            updateGallery();
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
                const displayName = removeExtension(imgName); // 无后缀名
                const div = document.createElement('div');
                div.className = 'showcase-item';
                div.innerHTML = `<img src="${{imgPath}}" alt="${{displayName}}" loading="lazy" onerror="this.src='${{imgPath}}'; this.onerror=null;"><p>${{displayName}}</p>`;
                showcaseImagesEl.appendChild(div);
            }});

            prevBtn.disabled = total <= 3;
            nextBtn.disabled = total <= 3;
        }}

        function updateGallery() {{
            const images = currentImages;
            const folder = currentNode.rel_path;
            galleryGridEl.innerHTML = '';

            if (images.length === 0) {{
                galleryGridEl.innerHTML = '<div class="no-images">暂无图片</div>';
                return;
            }}

            images.forEach(imgName => {{
                const fullPath = `${{folder}}/${{imgName}}`;
                let thumbPath = fullPath;
                if (ENABLE_THUMBNAIL) {{
                    thumbPath = `__thumbs__/${{folder}}/${{imgName}}`;
                }}

                const img = document.createElement('img');
                img.setAttribute('data-src', thumbPath);
                img.setAttribute('data-fullsrc', fullPath);
                img.alt = removeExtension(imgName); // 用于预览显示文件名

                img.onerror = function() {{
                    if (this.src !== this.getAttribute('data-fullsrc')) {{
                        this.src = this.getAttribute('data-fullsrc');
                        this.onerror = null;
                    }}
                }};

                // 鼠标移入：显示预览大图和文件名（无后缀）
                img.addEventListener('mouseenter', () => {{
                    previewImg.src = fullPath;
                    previewFilename.textContent = removeExtension(imgName);
                    previewContainer.style.display = 'block';
                }});
                img.addEventListener('mouseleave', () => {{
                    previewContainer.style.display = 'none';
                }});

                galleryGridEl.appendChild(img);
            }});

            // 强制前6张立即加载
            const imgs = galleryGridEl.querySelectorAll('img');
            for (let i = 0; i < Math.min(6, imgs.length); i++) {{
                const img = imgs[i];
                const dataSrc = img.getAttribute('data-src');
                if (dataSrc) {{
                    img.src = dataSrc;
                    img.removeAttribute('data-src');
                }}
            }}
            observeLazyImages();
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
if ENABLE_THUMBNAIL and HAS_PIL:
    print("🖼️ 缩略图功能已启用，网格显示缩略图，鼠标悬停预览原图并显示文件名（无后缀）。")
    print("📂 左侧导航已升级为清爽风格，并自动隐藏了 __thumbs__ 目录。")
elif not HAS_PIL and ENABLE_THUMBNAIL:
    print("⚠️ 缩略图未生成，将直接使用原图（可能加载较慢）。建议安装Pillow。")
else:
    print("⚡ 使用原图加载，若图片较多建议开启缩略图。")