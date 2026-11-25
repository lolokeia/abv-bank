import TOAST from './toast.js'
import API from './api_logic.js'

const auth_title = 'Ошибка авторизации'
document.addEventListener('DOMContentLoaded', () => {
            // --- ЛОГИКА ОТПРАВКИ ФОРМЫ (куда идет кнопка) ---
            const loginForm = document.getElementById('login-form');
            const loginInput = document.getElementById('login-input');
            const submitBtn = document.getElementById('submit-btn');
            const pinInput = document.getElementById('pin-input');

            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const loginValue = loginInput.value.trim();
                const pinValue = pinInput.value.trim();

                submitBtn.disabled = true;
                submitBtn.textContent = 'Вход...';

                try {
                    const resp = await API.login(loginValue, pinValue)
                
                    if (resp.status === 'ok') {
                        TOAST.infoToast(null, 'Успешный вход')
                        window.location.href = '/app.html'
                    } else {
                        const msg = await API.errResolve(resp.code)
                        TOAST.errorToast(auth_title, msg)
                    }
                } catch (error) {
                    console.error('Ошибка:', error);
                    TOAST.errorToast(null, 'Ошибка приема сообщения от сервера')
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Войти <span class="icon-arrow-right"></span>'
                }
            });
        });