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
THUMB_SIZE = (120, 120)                # 缩略图尺寸
THUMB_QUALITY = 70                      # WebP 质量
THUMB_ROOT = os.path.join(PHOTO_ROOT, '__suolve__')  # 缩略图存储目录
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

def generate_thumbnail(src_path, webp_path):
    """生成 WebP 缩略图，直接保存到指定路径"""
    try:
        os.makedirs(os.path.dirname(webp_path), exist_ok=True)

        with Image.open(src_path) as img:
            # 处理透明背景
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
                new_img.save(webp_path, 'WEBP', quality=THUMB_QUALITY, method=6)
            else:
                img.save(webp_path, 'WEBP', quality=THUMB_QUALITY, method=6)
        return True
    except Exception as e:
        print(f"   ✗ 缩略图生成失败: {src_path} -> {e}")
        return False

def collect_all_images(root_path):
    """递归收集所有图片文件，返回列表 [(完整路径, 相对路径), ...]"""
    images = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # 跳过 __thumbs__ 目录
        dirnames[:] = [d for d in dirnames if d != '__suolve__']
        for f in filenames:
            if f.lower().endswith(IMAGE_EXTENSIONS):
                full_path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(dirpath, root_path)
                if rel_path == '.':
                    rel_path = ''  # 根目录下的图片，相对路径为空
                images.append((full_path, rel_path))
    return images

def build_tree_from_images(images):
    """根据收集到的图片列表构建分类树结构"""
    tree = {}
    for full_path, rel_path in images:
        # 按相对路径拆分
        parts = rel_path.split(os.sep) if rel_path else []
        node = tree
        for i, part in enumerate(parts):
            if part not in node:
                node[part] = {}
            node = node[part]
        # 最后存储图片文件名（不含路径）
        if 'images' not in node:
            node['images'] = []
        node['images'].append(os.path.basename(full_path))

    # 将字典转换为列表格式
    def convert_to_list(node_dict, current_path=''):
        nodes = []
        for name, sub in node_dict.items():
            rel_path = os.path.join(current_path, name).replace('\\', '/') if current_path else name
            children = convert_to_list(sub, rel_path) if isinstance(sub, dict) else []
            images = sub.get('images', []) if isinstance(sub, dict) else []
            images.sort()
            node = {
                "name": name,
                "rel_path": rel_path,
                "images": images,
                "children": children
            }
            if images or children:
                nodes.append(node)
        return nodes

    return convert_to_list(tree)

print("🔍 正在扫描目录，收集所有图片...")
all_images = collect_all_images(PHOTO_ROOT)
if not all_images:
    print("❌ 未找到任何图片文件。")
    exit()

print(f"📸 找到 {len(all_images)} 张图片。")

if ENABLE_THUMBNAIL and HAS_PIL:
    print("🎨 开始生成 WebP 缩略图（首次可能较慢）...")
    for idx, (full_path, rel_path) in enumerate(all_images, 1):
        base_name = os.path.splitext(os.path.basename(full_path))[0]
        webp_path = os.path.join(THUMB_ROOT, rel_path, base_name + '.webp')
        # 检查是否需要生成缩略图
        if not os.path.exists(webp_path) or os.path.getmtime(full_path) > os.path.getmtime(webp_path):
            print(f"  [{idx}/{len(all_images)}] 生成: {webp_path}")
            generate_thumbnail(full_path, webp_path)
        else:
            print(f"  [{idx}/{len(all_images)}] 已存在: {webp_path}")
    print("✅ 缩略图处理完成。")
else:
    print("⚠️ 缩略图功能未启用或无Pillow库，将直接使用原图。")

print("🏗️ 正在构建相册树结构...")
tree = build_tree_from_images(all_images)
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
        body {{
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: #FEF5E7;
            color: #5D3A1A;
        }}
        #container {{ display: flex; min-height: 100vh; }}
        #sidebar {{
            width: 280px; background: #FFF9F0; color: #5D3A1A; padding: 24px 16px;
            box-shadow: 2px 0 12px rgba(0,0,0,0.05); overflow-y: auto; height: 100vh;
            position: sticky; top: 0; border-right: 1px solid #F0E4D0;
        }}
        #sidebar h2 {{ font-size: 1.3rem; font-weight: 600; margin-bottom: 24px; color: #C28E5D; padding-bottom: 12px; border-bottom: 2px solid #F0E4D0; }}
        .tree, .tree ul {{ list-style: none; margin: 0; padding-left: 0; }}
        .tree li {{ margin: 2px 0; line-height: 1.5; }}
        .tree .node-row {{ display: flex; align-items: center; padding: 6px 8px; border-radius: 8px; transition: background-color 0.15s; cursor: default; }}
        .tree .node-row:hover {{ background-color: #FDF3E6; }}
        .tree .icon {{ width: 28px; text-align: left; color: #C28E5D; font-size: 1rem; cursor: pointer; transition: color 0.15s; }}
        .tree .icon:hover {{ color: #E67E22; }}
        .tree .name {{ flex: 1; font-size: 0.95rem; color: #5D3A1A; padding: 2px 6px; border-radius: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; justify-content: space-between; }}
        .tree .name.clickable {{ cursor: pointer; }}
        .tree .name.clickable:hover {{ background-color: #FAEBD7; }}
        .tree .name.active {{ background-color: #E67E22; color: white; font-weight: 500; }}
        .tree .badge {{ background-color: #F5E6D3; color: #A55B2C; font-size: 0.7rem; font-weight: 500; padding: 2px 8px; border-radius: 30px; margin-left: 8px; }}
        .tree .name.active .badge {{ background-color: rgba(255,255,255,0.25); color: white; }}
        .tree .folder-content {{ margin-left: 28px; display: block; }}
        .tree .folder-content.collapsed {{ display: none; }}
        #main {{ flex: 1; padding: 24px; display: flex; flex-direction: column; }}
        #top-showcase {{ background: white; border-radius: 16px; padding: 20px; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.04); border: 1px solid #F5E6D3; }}
        #showcase-title {{ font-size: 1.1rem; font-weight: 600; color: #C28E5D; margin-bottom: 16px; }}
        #showcase-images {{ display: flex; justify-content: space-around; align-items: center; gap: 20px; }}
        .showcase-item {{ text-align: center; flex: 1; }}
        .showcase-item img {{ width: 100%; max-width: 200px; height: 150px; object-fit: cover; border-radius: 12px; box-shadow: 0 6px 14px rgba(0,0,0,0.08); }}
        .showcase-item p {{ margin-top: 8px; font-size: 0.85rem; color: #7F4F24; }}
        #showcase-controls {{ display: flex; justify-content: center; margin-top: 16px; gap: 12px; }}
        #showcase-controls button {{ background: white; border: 1px solid #E6B17E; color: #C28E5D; padding: 8px 22px; border-radius: 40px; cursor: pointer; font-size: 0.95rem; font-weight: 500; transition: all 0.15s; }}
        #showcase-controls button:hover {{ background: #FDF3E6; border-color: #E67E22; color: #E67E22; }}
        #showcase-controls button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
        #gallery {{ background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 16px rgba(0,0,0,0.04); border: 1px solid #F5E6D3; flex: 1; }}
        .gallery-grid {{ display: flex; flex-wrap: wrap; gap: 16px; justify-content: center; }}
        .gallery-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 120px;
            margin: 0 8px 16px 8px;
        }}
        .gallery-item img {{
            width: 120px;
            height: 120px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.04);
            cursor: pointer;
            transition: transform 0.15s, box-shadow 0.15s;
            border: 1px solid #F0E4D0;
        }}
        .gallery-item img:hover {{
            transform: scale(1.02);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }}
        .gallery-item span {{
            margin-top: 8px;
            font-size: 0.8rem;
            color: #7F4F24;
            text-align: center;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .no-images {{ text-align: center; color: #C28E5D; padding: 60px; font-size: 1rem; }}
    </style>
</head>
<body>
    <div id="container">
        <div id="sidebar">
            <h2>🍰 相册分类</h2>
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

    <script>
        const treeData = {tree_json};
        let currentNode = null;
        let currentImages = [];
        let showcaseStartIndex = 0;

        const treeEl = document.getElementById('category-tree');
        const showcaseImagesEl = document.getElementById('showcase-images');
        const galleryGridEl = document.getElementById('gallery-grid');
        const prevBtn = document.getElementById('prev-showcase');
        const nextBtn = document.getElementById('next-showcase');

        function removeExtension(filename) {{
            return filename.replace(/\\.[^/.]+$/, '');
        }}

        function getThumbPath(folder, imgName) {{
            const baseName = removeExtension(imgName);
            return `__thumbs__/${{folder}}/${{baseName}}.webp`;
        }}

        function renderAllImages() {{
            galleryGridEl.innerHTML = '';
            if (!currentImages || currentImages.length === 0) {{
                const noImgDiv = document.createElement('div');
                noImgDiv.className = 'no-images';
                noImgDiv.textContent = '暂无图片';
                galleryGridEl.appendChild(noImgDiv);
                return;
            }}
            const folder = currentNode.rel_path;
            for (let imgName of currentImages) {{
                const thumbPath = getThumbPath(folder, imgName);
                const displayName = removeExtension(imgName);

                const itemDiv = document.createElement('div');
                itemDiv.className = 'gallery-item';

                const img = document.createElement('img');
                img.src = thumbPath;
                img.alt = displayName;

                const nameSpan = document.createElement('span');
                nameSpan.textContent = displayName;

                itemDiv.appendChild(img);
                itemDiv.appendChild(nameSpan);
                galleryGridEl.appendChild(itemDiv);
            }}
        }}

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
                    iconSpan.innerHTML = '<i class="fas fa-folder"></i>';
                }} else {{
                    iconSpan.innerHTML = '<i class="fas fa-image"></i>';
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
            renderAllImages();
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
                const folder = currentNode.rel_path;
                const thumbPath = getThumbPath(folder, imgName);
                const displayName = removeExtension(imgName);
                const div = document.createElement('div');
                div.className = 'showcase-item';
                div.innerHTML = `<img src="${{thumbPath}}" alt="${{displayName}}" loading="lazy"><p>${{displayName}}</p>`;
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
print(f"🖼️ 缩略图目录结构与原照片完全一致，位于 {THUMB_ROOT}")
print(f"📱 所有图片一次性显示完毕，无滚动加载。")
print("🍰 已应用烘焙店风格配色，温馨舒适。")
print("💡 提示：现在只需上传 index.html 和 __thumbs__ 文件夹即可，GitHub 仓库大小将远低于 50MB。")