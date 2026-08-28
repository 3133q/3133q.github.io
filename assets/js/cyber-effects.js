/*
 * 赛博特效集合：粉色代码雨背景 / 点击彩蛋爆裂+涟漪 / 副标题打字机 / 顶部滚动进度条
 * 跟随明暗主题调整，并尊重 prefers-reduced-motion
 */
(function () {
    'use strict';

    var root = document.documentElement;
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function isDark() {
        return root.getAttribute('data-scheme') === 'dark';
    }

    function accentColor() {
        return getComputedStyle(root).getPropertyValue('--accent-color').trim() || '#4adeb2';
    }

    /* ================= 1. 粉色代码雨背景 ================= */
    if (!reducedMotion) {
        var canvas = document.createElement('canvas');
        canvas.id = 'matrix-rain';
        canvas.setAttribute('aria-hidden', 'true');
        document.body.prepend(canvas);
        var ctx = canvas.getContext('2d');

        var CHARS = '01{}[]<>$#;/\\|=+-*~^flagctf'.split('');
        // 彩蛋：整列掉落这些字符串
        var EASTER_WORDS = ['flag{y0u_f0und_m3}', 'sudo rm -rf', 'root@kali:~#', '0xDEADBEEF', 'pwned!', 'getshell'];
        var FONT_SIZE = 15;
        // 移动端：加大列间距、缩短拖尾，降低渲染压力
        var isMobile = window.matchMedia('(max-width: 640px)').matches;
        var COL_GAP = isMobile ? 44 : 30; // 列间距：越大越稀疏
        var TRAIL = isMobile ? 7 : 10;
        var W, H, COLS, cols;

        function resetColumn(i, initial) {
            cols[i] = {
                pos: initial ? Math.random() * -80 : -Math.random() * 30,
                word: Math.random() < 0.06
                    ? EASTER_WORDS[Math.floor(Math.random() * EASTER_WORDS.length)]
                    : null
            };
        }

        function resize() {
            W = canvas.width = window.innerWidth;
            H = canvas.height = window.innerHeight;
            COLS = Math.ceil(W / COL_GAP);
            cols = [];
            for (var i = 0; i < COLS; i++) resetColumn(i, true);
        }
        resize();
        window.addEventListener('resize', resize);

        // 标签页不可见时暂停渲染，省电省 CPU
        var rainTimer = null;
        var RAIN_INTERVAL = 80;
        function startRain() {
            if (rainTimer === null) {
                rainTimer = setInterval(drawRain, RAIN_INTERVAL);
            }
        }
        function stopRain() {
            clearInterval(rainTimer);
            rainTimer = null;
        }
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                stopRain();
            } else {
                startRain();
            }
        });

        // 用 (col,row) 生成稳定伪随机字符，拖尾字符不会闪烁
        function charAt(col, row) {
            var h = (col * 7349 + row * 15013) % CHARS.length;
            if (h < 0) h += CHARS.length;
            return CHARS[h];
        }

        function drawRain() {
            ctx.clearRect(0, 0, W, H);
            ctx.font = FONT_SIZE + 'px monospace';
            var base = isDark() ? 0.30 : 0.22;
            var color = accentColor();

            for (var i = 0; i < COLS; i++) {
                var c = cols[i];
                var headRow = Math.floor(c.pos);
                for (var t = 0; t < TRAIL; t++) {
                    var row = headRow - t;
                    if (row < 0 || row * FONT_SIZE > H) continue;

                    var ch;
                    if (c.word) {
                        // 彩蛋列：整列显示同一个字符串的连续字符
                        var idx = ((row % c.word.length) + c.word.length) % c.word.length;
                        ch = c.word.charAt(idx);
                    } else {
                        ch = charAt(i, row);
                    }

                    if (t === 0) {
                        // 头部字符：高亮 + 辉光（同色系浅/深一档）
                        ctx.globalAlpha = 1;
                        ctx.shadowColor = color;
                        ctx.shadowBlur = 10;
                        ctx.fillStyle = isDark() ? '#d9f8ea' : '#0b7c5d';
                    } else {
                        ctx.globalAlpha = base * (1 - t / TRAIL);
                        ctx.shadowBlur = 0;
                        ctx.fillStyle = color;
                    }
                    ctx.fillText(ch, i * COL_GAP, row * FONT_SIZE);
                }
                ctx.shadowBlur = 0;

                if (c.pos * FONT_SIZE > H + TRAIL * FONT_SIZE) {
                    resetColumn(i, false);
                }
                c.pos += c.word ? 0.35 : 0.5;
            }
            ctx.globalAlpha = 1;
        }

        startRain();
    }

    /* ================= 2. 点击彩蛋爆裂 + 涟漪 ================= */
    if (!reducedMotion) {
        var BURST_ITEMS = [
            // 网安/终端风
            'flag{', '}', '$', '#', '0x', '>', '~/', ';', 'pwn', 'CTF',
            'root', 'sudo', 'getshell', '提权成功', '+1s', '233',
            // 可爱向
            '♥', '★', '✦', '✧', '♪', 'nya~', '(≧▽≦)', '喵', 'biu~', '✿'
        ];
        var BURST_COLORS = ['#ff7eb6', '#4adeb2', '#64a5fa', '#c084fc', '#fbbf24', '#ff8fa3'];

        document.addEventListener('mousedown', function (e) {
            // 涟漪圈
            var ripple = document.createElement('div');
            ripple.className = 'click-ripple';
            ripple.style.left = e.clientX + 'px';
            ripple.style.top = e.clientY + 'px';
            ripple.style.borderColor = BURST_COLORS[Math.floor(Math.random() * BURST_COLORS.length)];
            document.body.appendChild(ripple);
            setTimeout(function () { ripple.remove(); }, 650);

            // 字符粒子
            var n = 9;
            for (var i = 0; i < n; i++) {
                var s = document.createElement('span');
                s.className = 'click-burst';
                s.textContent = BURST_ITEMS[Math.floor(Math.random() * BURST_ITEMS.length)];
                s.style.left = e.clientX + 'px';
                s.style.top = e.clientY + 'px';
                s.style.color = BURST_COLORS[Math.floor(Math.random() * BURST_COLORS.length)];
                s.style.fontSize = (11 + Math.random() * 7).toFixed(0) + 'px';
                var ang = Math.random() * Math.PI * 2;
                var dist = 36 + Math.random() * 70;
                s.style.setProperty('--tx', (Math.cos(ang) * dist).toFixed(1) + 'px');
                s.style.setProperty('--ty', (Math.sin(ang) * dist - 34).toFixed(1) + 'px');
                s.style.setProperty('--rot', (Math.random() * 90 - 45).toFixed(0) + 'deg');
                document.body.appendChild(s);
                (function (el) {
                    setTimeout(function () { el.remove(); }, 950);
                })(s);
            }
        });
    }

    /* ================= 3. 副标题打字机 ================= */
    var desc = document.querySelector('.site-description');
    if (desc && !reducedMotion) {
        var phrases = [
            desc.textContent.trim(),
            'Web · PWN · Reverse · Crypto · Misc',
            'flag{keep_hacking_keep_learning}',
            '正在入侵知识库… 100%'
        ];
        desc.classList.add('typing');
        var pi = 0, ci = phrases[0].length, deleting = false;

        function tick() {
            var phrase = phrases[pi];
            if (!deleting) {
                ci++;
                if (ci >= phrase.length) {
                    ci = phrase.length;
                    deleting = true;
                    desc.textContent = phrase;
                    setTimeout(tick, 2200);
                    return;
                }
            } else {
                ci--;
                if (ci <= 0) {
                    ci = 0;
                    deleting = false;
                    pi = (pi + 1) % phrases.length;
                }
            }
            desc.textContent = phrases[pi].slice(0, ci) || ' ';
            setTimeout(tick, deleting ? 35 : 85);
        }
        setTimeout(tick, 2500);
    }

    /* ================= 5. Hero 标题逐字弹入 + 标语打字机轮播 ================= */
    var heroTitle = document.querySelector('.hero-title');
    if (heroTitle && !reducedMotion) {
        var titleText = heroTitle.textContent;
        heroTitle.textContent = '';
        heroTitle.setAttribute('aria-label', titleText);
        for (var i = 0; i < titleText.length; i++) {
            var sp = document.createElement('span');
            sp.className = 'hero-char';
            sp.textContent = titleText[i] === ' ' ? ' ' : titleText[i];
            sp.style.animationDelay = (0.4 + i * 0.08) + 's';
            heroTitle.appendChild(sp);
        }
    }

    var heroSub = document.querySelector('.hero-subtitle');
    if (heroSub && !reducedMotion) {
        var heroPhrases = [
            'CTF 萌新 · PWN 方向修行中',
            'flag{keep_hacking_keep_learning}',
            '栈里来，堆里去，万物皆可溢出',
            'We will all move forward.',
            '正在调试人生 …… 未发现段错误'
        ];
        heroSub.classList.add('typing');
        var hp = 0, hc = 0, hDeleting = false;

        function heroTick() {
            var phrase = heroPhrases[hp];
            if (!hDeleting) {
                hc++;
                if (hc >= phrase.length) {
                    hc = phrase.length;
                    hDeleting = true;
                    heroSub.textContent = phrase;
                    setTimeout(heroTick, 2600);
                    return;
                }
            } else {
                hc--;
                if (hc <= 0) {
                    hc = 0;
                    hDeleting = false;
                    hp = (hp + 1) % heroPhrases.length;
                }
            }
            heroSub.textContent = heroPhrases[hp].slice(0, hc) || ' ';
            setTimeout(heroTick, hDeleting ? 30 : 95);
        }
        // 等标题逐字弹入差不多结束再开始打字
        setTimeout(heroTick, 1800);
    }

    /* ================= 4. 顶部滚动进度条 ================= */
    var bar = document.createElement('div');
    bar.id = 'scroll-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    function updateBar() {
        var h = document.documentElement;
        var max = h.scrollHeight - h.clientHeight;
        var pct = max > 0 ? (h.scrollTop / max) * 100 : 0;
        bar.style.width = pct + '%';
    }
    document.addEventListener('scroll', updateBar, { passive: true });
    updateBar();

    /* ================= 6. 返回顶部按钮 ================= */
    var topBtn = document.createElement('button');
    topBtn.id = 'back-to-top';
    topBtn.type = 'button';
    topBtn.setAttribute('aria-label', '返回顶部');
    topBtn.innerHTML =
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">' +
        '<polyline points="18 15 12 9 6 15"></polyline></svg>';
    document.body.appendChild(topBtn);

    function toggleTopBtn() {
        var h = document.documentElement;
        topBtn.classList.toggle('visible', h.scrollTop > 480);
    }
    document.addEventListener('scroll', toggleTopBtn, { passive: true });
    toggleTopBtn();

    topBtn.addEventListener('click', function () {
        var smooth = !reducedMotion;
        window.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
    });
})();
