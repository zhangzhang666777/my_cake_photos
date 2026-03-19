import os
import json

# ========== 配置部分 ==========
PHOTO_ROOT = "D:/my_cake_photos"      # 照片根目录，其下的所有子文件夹（不限层级）都会作为分类
OUTPUT_FILE = "index.html"            # 生成的HTML文件名
TITLE = "华味嘉蛋糕电子相册"                  # 网页标题

# 支持的图片格式
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
# ==============================

def build_tree(current_path, rel_path=""):
    """递归构建树，返回节点列表，每个节点包含 name, rel_path, images, children"""
    nodes = []
    try:
        items = os.listdir(current_path)
    except PermissionError:
        return nodes
    for item in sorted(items):
        item_path = os.path.join(current_path, item)
        if os.path.isdir(item_path):
            child_rel = os.path.join(rel_path, item) if rel_path else item
            children = build_tree(item_path, child_rel)
            # 当前文件夹下的图片
            images = []
            for file in os.listdir(item_path):
                file_path = os.path.join(item_path, file)
                if os.path.isfile(file_path) and file.lower().endswith(IMAGE_EXTENSIONS):
                    images.append(file)
            images.sort()
            node = {
                "name": item,
                "rel_path": child_rel.replace('\\', '/'),  # 统一为斜杠，用于HTML路径
                "images": images,
                "children": children
            }
            # 只有当有图片或有子文件夹时才添加（避免空文件夹）
            if images or children:
                nodes.append(node)
    return nodes

tree = build_tree(PHOTO_ROOT)
if not tree:
    print("没有找到任何图片分类，请检查根目录下是否有包含图片的子文件夹。")
    exit()

tree_json = json.dumps(tree, ensure_ascii=False)

# ==================== 生成HTML ====================
html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{TITLE}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
        }}
        #container {{
            display: flex;
            min-height: 100vh;
        }}
        /* 左侧树形导航 */
        #sidebar {{
            width: 260px;
            background-color: #333;
            color: white;
            padding: 20px;
            overflow-y: auto;
        }}
        #sidebar h2 {{
            margin-bottom: 20px;
            font-size: 1.4em;
            border-bottom: 2px solid #555;
            padding-bottom: 10px;
        }}
        .tree, .tree ul {{
            list-style: none;
            margin: 0;
            padding-left: 20px;
        }}
        .tree li {{
            margin: 5px 0;
            cursor: default;
            user-select: none;
        }}
        .tree .node-folder {{
            font-weight: bold;
            color: #ddd;
        }}
        .tree .node-leaf {{
            color: #aaa;
        }}
        .tree .node-folder.clickable, .tree .node-leaf.clickable {{
            cursor: pointer;
        }}
        .tree .node-folder.clickable:hover, .tree .node-leaf.clickable:hover {{
            color: white;
        }}
        .tree .active {{
            background-color: #007bff;
            color: white !important;
            border-radius: 4px;
            padding: 2px 5px;
        }}
        .tree .toggle {{
            display: inline-block;
            width: 16px;
            text-align: center;
            cursor: pointer;
            color: #aaa;
        }}
        .tree .toggle:hover {{
            color: white;
        }}
        .tree .folder-content {{
            display: block;
        }}
        .tree .folder-content.collapsed {{
            display: none;
        }}
        /* 右侧主内容区 */
        #main {{
            flex: 1;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }}
        #top-showcase {{
            background-color: #fff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        #showcase-title {{
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #333;
        }}
        #showcase-images {{
            display: flex;
            justify-content: space-around;
            align-items: center;
            gap: 20px;
        }}
        .showcase-item {{
            text-align: center;
            flex: 1;
        }}
        .showcase-item img {{
            width: 100%;
            max-width: 200px;
            height: 150px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .showcase-item p {{
            margin-top: 8px;
            font-size: 0.9em;
            color: #666;
        }}
        #showcase-controls {{
            display: flex;
            justify-content: center;
            margin-top: 15px;
        }}
        #showcase-controls button {{
            background-color: #007bff;
            color: white;
            border: none;
            padding: 8px 20px;
            margin: 0 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
        }}
        #showcase-controls button:hover {{
            background-color: #0056b3;
        }}
        #showcase-controls button:disabled {{
            background-color: #ccc;
            cursor: not-allowed;
        }}
        #gallery {{
            background-color: #fff;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            flex: 1;
        }}
        .gallery-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
        }}
        .gallery-grid img {{
            width: 200px;
            height: 200px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            cursor: pointer;
            transition: box-shadow 0.2s;
            background-color: #f5f5f5;  /* 占位背景 */
        }}
        .gallery-grid img:hover {{
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        }}
        .no-images {{
            text-align: center;
            color: #999;
            padding: 50px;
            font-size: 1.2em;
        }}
        #preview-container {{
            display: none;
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: white;
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
            z-index: 1000;
            max-width: 80vw;
            max-height: 80vh;
        }}
        #preview-img {{
            display: block;
            max-width: 100%;
            max-height: 70vh;
            object-fit: contain;
        }}
        /* 懒加载过渡效果（可选） */
        .gallery-grid img[src=""] {{
            opacity: 0.5;
        }}
        .gallery-grid img {{
            transition: opacity 0.2s;
        }}
    </style>
</head>
<body>
    <div id="container">
        <!-- 左侧树形分类导航 -->
        <div id="sidebar">
            <h2>相册分类</h2>
            <ul class="tree" id="category-tree"></ul>
        </div>

        <!-- 右侧主内容区 -->
        <div id="main">
            <div id="top-showcase">
                <div id="showcase-title">精选展示</div>
                <div id="showcase-images"></div>
                <div id="showcase-controls">
                    <button id="prev-showcase" onclick="prevShowcase()">❮ 上一组</button>
                    <button id="next-showcase" onclick="nextShowcase()">下一组 ❯</button>
                </div>
            </div>
            <div id="gallery">
                <div id="gallery-grid" class="gallery-grid"></div>
            </div>
        </div>
    </div>

    <div id="preview-container">
        <img id="preview-img" src="" alt="预览">
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
        const previewContainer = document.getElementById('preview-container');
        const previewImg = document.getElementById('preview-img');

        // ---------- 懒加载 Intersection Observer ----------
        const lazyObserver = new IntersectionObserver((entries, observer) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const img = entry.target;
                    const dataSrc = img.getAttribute('data-src');
                    if (dataSrc) {{
                        img.src = dataSrc;
                        img.removeAttribute('data-src');
                        // 可选：加载完成后停止观察
                        observer.unobserve(img);
                    }}
                }}
            }});
        }}, {{
            rootMargin: '100px',   // 提前100px加载，提升体验
            threshold: 0.01
        }});

        // 观察所有带 data-src 的图片
        function observeLazyImages() {{
            document.querySelectorAll('img[data-src]').forEach(img => lazyObserver.observe(img));
        }}

        // 递归渲染树
        function renderTree(nodes, parentElement, level = 0) {{
            nodes.forEach(node => {{
                const li = document.createElement('li');
                li.style.paddingLeft = (level * 20) + 'px';
                li.dataset.path = node.rel_path;  // 存储路径，用于高亮定位

                const hasChildren = node.children && node.children.length > 0;
                const hasImages = node.images && node.images.length > 0;

                if (hasChildren) {{
                    // 文件夹节点：有子文件夹
                    const toggleSpan = document.createElement('span');
                    toggleSpan.className = 'toggle';
                    toggleSpan.textContent = '▼'; // 默认展开
                    toggleSpan.onclick = function(e) {{
                        e.stopPropagation();
                        const content = li.querySelector('.folder-content');
                        if (content) {{
                            if (content.style.display === 'none') {{
                                content.style.display = 'block';
                                toggleSpan.textContent = '▼';
                            }} else {{
                                content.style.display = 'none';
                                toggleSpan.textContent = '▶';
                            }}
                        }}
                    }};
                    li.appendChild(toggleSpan);

                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'node-folder' + (hasImages ? ' clickable' : '');
                    nameSpan.textContent = node.name + (hasImages ? ` (${{node.images.length}})` : '');
                    if (hasImages) {{
                        nameSpan.addEventListener('click', (e) => {{
                            e.stopPropagation();
                            document.querySelectorAll('.tree .active').forEach(el => el.classList.remove('active'));
                            li.classList.add('active');
                            switchNode(node);
                        }});
                    }}
                    li.appendChild(nameSpan);

                    const childUl = document.createElement('ul');
                    childUl.className = 'folder-content';
                    li.appendChild(childUl);
                    renderTree(node.children, childUl, level + 1);
                }} else if (hasImages) {{
                    // 叶子节点：只有图片，无子文件夹
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'node-leaf clickable';
                    nameSpan.textContent = node.name + ` (${{node.images.length}})`;
                    nameSpan.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        document.querySelectorAll('.tree .active').forEach(el => el.classList.remove('active'));
                        li.classList.add('active');
                        switchNode(node);
                    }});
                    li.appendChild(nameSpan);
                }} else {{
                    // 既无图片也无子文件夹，不显示
                    return;
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
                const div = document.createElement('div');
                div.className = 'showcase-item';
                // 展示区图片数量少，直接加载
                div.innerHTML = `<img src="${{imgPath}}" alt="${{imgName}}" loading="lazy"><p>${{imgName}}</p>`;
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
                const imgPath = `${{folder}}/${{imgName}}`;
                const img = document.createElement('img');
                // 不直接设置 src，使用 data-src 实现懒加载
                img.setAttribute('data-src', imgPath);
                img.alt = imgName;
                // 可选的占位背景通过 CSS 显示
                img.style.backgroundColor = '#eee';

                // 预览功能：鼠标移入时加载预览图（如果尚未加载，则临时加载）
                img.addEventListener('mouseenter', () => {{
                    // 如果图片还没加载（src为空），先临时设置src用于预览，但不影响懒加载逻辑
                    if (!img.src) {{
                        // 可以临时加载，但为了不重复请求，最好使用已经加载的图片
                        // 简单起见：如果图片未加载，预览时直接使用 data-src
                        previewImg.src = img.getAttribute('data-src') || imgPath;
                    }} else {{
                        previewImg.src = img.src;
                    }}
                    previewContainer.style.display = 'block';
                }});
                img.addEventListener('mouseleave', () => {{
                    previewContainer.style.display = 'none';
                }});

                galleryGridEl.appendChild(img);
            }});

            // 新生成的图片需要被 observer 观察
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

        // 初始化：渲染树并选中第一个有图片的节点
        window.onload = function() {{
            renderTree(treeData, treeEl);

            // 深度优先查找第一个有图片的节点
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
                    // 高亮对应的li
                    const lis = document.querySelectorAll('.tree li');
                    for (let li of lis) {{
                        if (li.dataset.path === firstNode.rel_path) {{
                            li.classList.add('active');
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
print("📂 树形分类已生成，支持多级子文件夹。")
print("⚡ 优化：图片已启用懒加载，滚动到可视区域时才会加载，首屏加载速度大幅提升。")