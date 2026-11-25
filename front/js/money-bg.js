(function () {
    const isMobile = window.matchMedia("(max-width: 768px)").matches || navigator.maxTouchPoints > 0;
    const canvas = document.getElementById("money-bg");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    // 1. Читаем настройки из HTML (с запасными значениями по умолчанию)
    const ds = canvas.dataset;
    const CONFIG = {
    count: parseInt(ds.count) || 80,
    color: ds.color || "#2edd2e",
    words: ds.words ? ds.words.split(",") : ["₽", "$", "€", "₿"],
    bills: ds.bills ? ds.bills.split(",") : ["АБВ-БАНК"],
    billChance: parseFloat(ds.billChance) || 0.3, // Вероятность купюры (0.3 = 30%)
    speedMult: parseFloat(ds.speed) || 1.0,
    parallax: parseFloat(ds.parallax) || 0.1,
    mouseRadius: parseFloat(ds.mouseRadius) || 130
    };

    if (isMobile) {
        CONFIG.count = Math.floor(CONFIG.count / 3)
    }

    const debug_msg = document.querySelector(".debug_msg")
    // 2. Запекаем слова и купюры в скрытые канвасы (Спрайты)
    // Это убирает лаги: текст рисуется 1 раз при старте, а не 60 раз в секунду
    function createSprite(text, isBill) {
    const offCanvas = document.createElement("canvas");
    const oCtx = offCanvas.getContext("2d");
    const scale = 2; // Рисуем в 2x качестве, чтобы при приближении не мылилось

    oCtx.font = `bold ${(isBill ? 12 : 22) * scale}px Arial`;
    const textWidth = oCtx.measureText(text).width;

    const w = isBill ? Math.max(40 * scale, textWidth + 16 * scale) : textWidth + 10 * scale;
    const h = (isBill ? 20 : 28) * scale;

    offCanvas.width = w;
    offCanvas.height = h;

    // Повторно задаем шрифт после изменения размера канваса
    oCtx.font = `bold ${(isBill ? 12 : 22) * scale}px Arial`;
    oCtx.textAlign = "center";
    oCtx.textBaseline = "middle";
    oCtx.strokeStyle = CONFIG.color;
    oCtx.fillStyle = CONFIG.color;
    oCtx.lineWidth = 1.5 * scale;

    if (isBill) {
    oCtx.globalAlpha = 0.2;
    oCtx.fillRect(2, 2, w - 4, h - 4);
    oCtx.globalAlpha = 1.0;
    oCtx.strokeRect(2, 2, w - 4, h - 4);
    }

    oCtx.fillText(text, w / 2, h / 2);

    return { img: offCanvas, baseW: w / scale, baseH: h / scale };
    }

    // Генерируем пул готовых картинок при загрузке
    const wordSprites = CONFIG.words.map(w => createSprite(w.trim(), false));
    const billSprites = CONFIG.bills.map(b => createSprite(b.trim(), true));

    // 3. Размеры экрана и мышь
    let width, height;
    const mouse = { x: -1000, y: -1000, targetX: 0, targetY: 0, curX: 0, curY: 0 };

    function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    }
    window.addEventListener("resize", resize);
    resize();

    window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    mouse.targetX = (e.clientX - width / 2) * CONFIG.parallax;
    mouse.targetY = (e.clientY - height / 2) * CONFIG.parallax;
    });

    // 4. Создание и сброс частицы (без пересоздания объектов в памяти)
    function resetItem(p, randomY = false) {
    const z = Math.random() * 1.6 + 0.4; // Глубина от 0.4 до 2.0
    const isBill = Math.random() < CONFIG.billChance;
    const pool = isBill ? billSprites : wordSprites;

    p.baseX = Math.random() * width;
    p.y = randomY ? Math.random() * height : -60;
    p.z = z;
    p.speedY = (Math.random() * 60 + 50) * z * CONFIG.speedMult; // Пикселей в секунду
    p.swayPhase = Math.random() * Math.PI * 2;
    p.swaySpeed = Math.random() * 1.5 + 1.0;
    p.angle = Math.random() * Math.PI * 2;
    p.spin = (Math.random() - 0.5) * 1.5;
    p.vx = 0;
    p.vy = 0;
    p.sprite = pool[Math.floor(Math.random() * pool.length)];
    return p;
    }

    // Заполняем массив один раз при старте
    const items = Array.from({ length: CONFIG.count }, () => resetItem({}, true));

    // 5. Игровой цикл с deltaTime
    let lastTime = performance.now();
    const radiusSq = CONFIG.mouseRadius * CONFIG.mouseRadius;

    let frame = 0;
    let fps = 0;
    let last_sec = performance.now();

    function animate(now) {
    const dt = Math.min((now - lastTime) / 1000, 0.05);
    lastTime = now;

    ctx.clearRect(0, 0, width, height);

    // Плавный параллакс
    mouse.curX += (mouse.targetX - mouse.curX) * 5 * dt;
    mouse.curY += (mouse.targetY - mouse.curY) * 5 * dt;
    
    // Дебаг счетчик фпс
    frame++;
    frametime = now - last_sec
    if (frametime >= 1000) {
        fps = frame;
        frame = 0;
        last_sec = now;
    }
    if (debug_msg) {
        debug_msg.textContent = `FPS: ${fps} | dT: ${dt.toFixed(4)}`;
    }
    
    for (let i = 0; i < items.length; i++) {
    const p = items[i];

    // --- ЗДЕСЬ ТВОЯ ФИЗИКА ---
    p.y += (p.speedY + p.vy) * dt;
    p.baseX += p.vx * dt;
    p.swayPhase += p.swaySpeed * dt;
    p.angle += p.spin * dt;

    // Затухание инерции
    p.vx *= Math.pow(0.05, dt);
    p.vy *= Math.pow(0.05, dt);

    const drawX = p.baseX + Math.sin(p.swayPhase) * 25 * p.z - mouse.curX * p.z;
    const drawY = p.y - mouse.curY * p.z;

    // Отталкивание от мыши (без тяжелого Math.hypot для далеких частиц)
    if (!isMobile){
    const dx = drawX - mouse.x;
    const dy = drawY - mouse.y;
    const distSq = dx * dx + dy * dy;

    if (distSq < radiusSq && distSq > 0) {
    const dist = Math.sqrt(distSq);
    const force = (CONFIG.mouseRadius - dist) / CONFIG.mouseRadius;
    p.vx += (dx / dist) * force * 400 * p.z * dt;
    p.vy += (dy / dist) * force * 400 * p.z * dt;
    }}

    // Возврат наверх
    if (p.y > height + 80) {
    resetItem(p, false);
    continue;
    }

    // --- ОТРИСОВКА ---
    const w = p.sprite.baseW * p.z;
    const h = p.sprite.baseH * p.z;

    ctx.save();
    ctx.globalAlpha = Math.min(p.z * 0.45, 0.9);
    ctx.translate(drawX, drawY);
    ctx.rotate(p.angle);
    ctx.drawImage(p.sprite.img, -w / 2, -h / 2, w, h);
    ctx.restore();
 }

 requestAnimationFrame(animate);
 }
 
 requestAnimationFrame(animate);
 })();