document.addEventListener("DOMContentLoaded", () => {
  // Ключ, по которому браузер запомнит, что пользователь закрыл баннер
  const STORAGE_KEY = "abv_bank_notice";

 //1. Проверяем: если пользователь уже нажимал кнопку, ничего не делаем
  if (localStorage.getItem(STORAGE_KEY) === "true") {
   return;
  }

  // 2. Создаём контейнер для баннера
  const banner = document.createElement("div");
  banner.id = "abv-cookie-banner";

  // 3. Прописываем HTML-разметку и стили прямо внутри JS
  banner.innerHTML = `
    <style>
      #abv-cookie-banner {
        position: fixed !important;
        bottom: 24px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: calc(100% - 40px) !important;
        max-width: 700px !important;
        background: rgba(18, 18, 22, 0.94) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid #4caf50 !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6) !important;
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
        gap: 20px !important;
        z-index: 9999 !important;
        color: #e0e0e6 !important;
        font-family: sans-serif !important;
        font-size: 13px !important;
        line-height: 1.45 !important;
        box-sizing: border-box !important;
        margin: 0 !important;
      }

      #abv-cookie-banner strong {
        color: #ffffff !important;
      }

      #abv-cookie-banner .abv-cookie-text {
        position: static !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: left !important;
      }

      #abv-cookie-banner .abv-cookie-actions {
        position: static !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        flex-shrink: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
      }

      #abv-cookie-banner .abv-cookie-btn {
        position: static !important;
        display: block !important;
        margin: 0 !important;
        padding: 8px 16px !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 13px !important;
        line-height: 1.2 !important;
        text-align: center !important;
        cursor: pointer !important;
        white-space: nowrap !important;
        user-select: none !important;
        transition: all 0.25s ease !important;
        box-sizing: border-box !important;
      }

      #abv-cookie-terms {
        background: transparent !important;
        color: #e2e2e2 !important;
        border: 1px solid #4caf50 !important;
      }

      #abv-cookie-terms:hover {
        background: #2ad32f !important;
        color: #121216 !important;
        box-shadow: 0 0 15px rgba(46, 221, 46, 0.6) !important;
      }

      #abv-cookie-accept {
        background: transparent !important;
        color: #e2e2e2 !important;
        border: 1px solid #4caf50 !important;
      }

      #abv-cookie-accept:hover {
        background: #2ad32f !important;
        color: #121216 !important;
        box-shadow: 0 0 15px rgba(46, 221, 46, 0.6) !important;
      }

      @media (max-width: 550px) {
        #abv-cookie-banner {
          flex-direction: column !important;
          align-items: stretch !important;
        }
        #abv-cookie-banner .abv-cookie-text {
          text-align: center !important;
        }
        #abv-cookie-banner .abv-cookie-actions {
          flex-direction: row !important;
          justify-content: center !important;
        }
      }
    </style>

    <div>
      <strong>Дисклеймер:</strong> Это симулятор банка для дипломной/курсовой работы, банк не реален. 
      Не вводите реальные имена/пин-коды или любые другие конфиденциальные данные.
      Я использую ваши куки для сохранения сессии и прочих штучек, спасибо за внимание.
    </div>
    <div class="abv-cookie-actions">
      <span id="abv-cookie-terms" class="abv-cookie-btn" role="button" tabindex="0">Подробнее</span>
      <span id="abv-cookie-accept" class="abv-cookie-btn" role="button" tabindex="0">Согласен</span>
    </div>
  `;

  // 4. Добавляем готовый баннер на страницу
  document.body.appendChild(banner);

  document.getElementById("abv-cookie-terms").addEventListener("click", () => {
    window.location.href = "/terms";
  });
  // 5. Вешаем обработчик на кнопку закрытия
  document.getElementById("abv-cookie-accept").addEventListener("click", () => {
    localStorage.setItem(STORAGE_KEY, "true");
    banner.remove();
  });
});
