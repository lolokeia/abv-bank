document.addEventListener("DOMContentLoaded", function () {
    const footerHTML = `
        <footer>
            <div class="footer-bottom">
                <p>1789-2077 АБВ-БАНК ltd. Все права не защищены. Не является лекарством. &copy;2026-2027 lolokeia </p>
                <p><a href="/terms" style="color: #2ecc71; text-decoration: none;">Отказ от ответственности</a></p>
            </div>
        </footer>
    `;
    document.body.insertAdjacentHTML("beforeend", footerHTML);
});