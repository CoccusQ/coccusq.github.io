// 侧边栏功能
class DocSidebar {
    constructor() {
        this.sidebar = document.querySelector('.sidebar');
        this.navContainer = document.getElementById('sidebar-nav');
        this.toggleButton = document.querySelector('.sidebar-toggle');
        this.headers = [];
        this.observer = null;
        this.activeItem = null;

        this.init();
    }

    init() {
        // 获取所有标题
        this.collectHeaders();
        // 生成目录
        this.generateTOC();
        // 初始化交互
        this.initEvents();
        // 初始化滚动监听
        this.initIntersectionObserver();
    }

    collectHeaders() {
        const mainContent = document.querySelector('.main-content');
        this.headers = Array.from(mainContent.querySelectorAll('h1, h2, h3, h4, h5, h6'))
            .filter(header => header.id)
            .map(header => ({
                id: header.id,
                text: header.innerText,
                level: parseInt(header.tagName.substring(1))
            }));
    }

    // 修改目录生成逻辑
    generateTOC() {
        let html = '';
        let stack = [];

        this.headers.forEach(header => {
            while (stack.length > 0 && stack[stack.length - 1].level >= header.level) {
                html += '</ul>';
                stack.pop();
            }

            if (stack.length === 0 || header.level > stack[stack.length - 1].level) {
                html += '<ul>';
                stack.push(header);
            }

            html += `<li><a href="#${header.id}">${header.text}</a>`;
        });

        this.navContainer.innerHTML = html + '</ul>'.repeat(stack.length);
    }

    initEvents() {
        // 点击目录平滑滚动
        this.navContainer.addEventListener('click', (e) => {
            if (e.target.tagName === 'A') {
                e.preventDefault();
                const targetId = e.target.getAttribute('href');
                const target = document.querySelector(targetId);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });

        // 移动端切换按钮
        this.toggleButton.addEventListener('click', () => {
            this.sidebar.classList.toggle('active');
        });
    }

    // 在DocSidebar类中添加
    initCollapse() {
        this.navContainer.addEventListener('click', (e) => {
            const listItem = e.target.closest('li');
            if (listItem && listItem.children.length > 1) {
                listItem.classList.toggle('collapsed');
            }
        });
    }

    initIntersectionObserver() {
        const options = {
            rootMargin: '-50px 0px -50% 0px',
            threshold: 0
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const id = entry.target.id;
                const navItem = this.navContainer.querySelector(`a[href="#${id}"]`);

                if (entry.isIntersecting) {
                    if (this.activeItem) {
                        this.activeItem.parentElement.classList.remove('active');
                    }
                    navItem.parentElement.classList.add('active');
                    this.activeItem = navItem;
                }
            });
        }, options);

        // 观察所有标题元素
        this.headers.forEach(header => {
            const element = document.getElementById(header.id);
            if (element) this.observer.observe(element);
        });
    }
}

// 初始化侧边栏
document.addEventListener('DOMContentLoaded', () => {
    new DocSidebar();
});

// 保持原有滚动监听
window.addEventListener('scroll', function () {
    const navbar = document.querySelector('.navbar');
    navbar.classList.toggle('scrolled', window.scrollY > 50);
});


// 复制功能实现
document.addEventListener('DOMContentLoaded', function () {
    // 为每个代码块添加按钮
    document.querySelectorAll('pre').forEach(pre => {
        const btn = document.createElement('button');
        btn.className = 'code-copy-btn';
        btn.textContent = '复制';

        // 插入按钮
        pre.style.position = 'relative';
        pre.appendChild(btn);

        // 绑定点击事件
        btn.addEventListener('click', async () => {
            const code = pre.querySelector('code').innerText;
            try {
                await navigator.clipboard.writeText(code);
                showFeedback('✅ 代码已复制到剪贴板');
                btn.textContent = '已复制!';
                setTimeout(() => {
                    btn.textContent = '复制';
                }, 2000);
            } catch (err) {
                showFeedback('❌ 复制失败，请手动选择复制');
                console.error('复制失败:', err);
            }
        });
    });

    // 显示提示
    function showFeedback(text) {
        const feedback = document.getElementById('copyFeedback');
        feedback.textContent = text;
        feedback.style.display = 'block';
        setTimeout(() => {
            feedback.style.display = 'none';
        }, 2000);
    }
});