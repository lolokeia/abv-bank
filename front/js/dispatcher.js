import TOAST from './toast.js'
import API from './api_logic.js'

const authErr = 'Ошибка авторизации'

const actions = {
    async login(btn) {
        const loginInput = document.getElementById('log-login-input').value
        const pinInput = document.getElementById('log-pin-input').value

        const resp = await API.login(loginInput, pinInput)
        if (resp.status === 'ok') {
            TOAST.infoToast(undefined, 'Вход успешен')
            window.location.href = '/app'
        }
        else {
            TOAST.errorToast(authErr, await API.errResolve(resp.code))
        }
    },

    async register(btn) {
        const loginInput = document.getElementById('reg-login-input').value
        const nameInput = document.getElementById('reg-name-input').value
        const pinInput = document.getElementById('reg-pin-input').value
        const pinConfirm = document.getElementById('reg-pin-confirm').value;

        if (pinInput !== pinConfirm) {
            TOAST.errorToast('Ошибка', 'Пин-коды не совпадают');
            return;
        }

        const resp = await API.register(loginInput, nameInput, pinInput)
        if (resp.status === 'ok') {
            TOAST.infoToast('Успех', 'Регистрация успешна')
            window.location.href = '/app'
        }
        else {
            TOAST.errorToast(authErr, await API.errResolve(resp.code))
        }

    },

    toggle_password(btn) {
        const card = btn.closest('.input-card');
        
        const input = card.querySelector('input');
        
        const icon = btn.querySelector('span');

        const isPassword = input.type === 'password';

        input.type = isPassword ? 'text' : 'password';

        if (isPassword) {
            icon.classList.add('icon-eye-off');
            btn.setAttribute('aria-label', 'Скрыть пароль');
        } else {
            icon.classList.remove('icon-eye-off');
            btn.setAttribute('aria-label', 'Показать пароль');
        }
    },

    toggle_register() {
        const loginSection = document.querySelector('.login');
        const registerSection = document.querySelector('.register');

        if (!loginSection.hidden) {
            loginSection.hidden = true;
            registerSection.hidden = false;
        } else {
            loginSection.hidden = false;
            registerSection.hidden = true;
        }
    },

    forgot_pin(btn) {
        TOAST.createToast('неа', 'эмм. ну короче эта функция еще не реализована. Если вы нажали сюда случайно или по приколу, то это ненормально. Вы зачем вообще тыкаете на всякие кнопки? А вдруг она ядерку вызовет и удалит к чертям ваш аккаунт? Вы об этом подумали а? Несите ответственность за свои действия, уже не маленькие ведь. Если вы нажали сюда потому что реально забыли пароль - поплачьте. Возможно мы вас услышим. спасибо за внимание.', 15000, '#000070', '#0000FF')
        TOAST.createToast('неа x2', 'Если предыдущее сообщение вызвало у вас сильную фрустрацию - поплачьте об этом x2. И думайте прежде чем тыкать. Вообще вы бы могли обратиться в поддержку, но у нас её нет, так как я не хочу хранить ваши конфиденциальные данные (да и мне лень писать мессенджер). А если серьезно - скоро фича будет.', 30000, '#700070', '#FF00FF')
        TOAST.createToast('что', 'Зачем вы вообще нажали эту кнопку? что вообще такое кнопка, а что такое сайт? что такое небо? что такое мир? Зачем вам потребовалось нажать на кнопку восстановления пароля? Вы забыли пароль? Так это даже не пароль, это ПИН-код. 4 цифры всего. У вас деменция? Альцгеймер? Или вы просто не стали запоминать пароль и переложили ответственность на менеджер паролей?', 45000, '#6e7000', '#ffe600')
        TOAST.createToast('зачем', 'Я же уверен, что вы этот текст даже не читаете, потому что вам просто лень. Правильно, "он что не мог просто написать "Скоро будет", вот дурачёк какой-то, написал тут кучу букав, а нам читать" да? Ленивые людишки (Если вы читали, проигнорируйте это сообщение)', 60000,  '#006c70', '#00eeff')
        TOAST.createToast('Обэмэ', 'Обэмэ', 61000, '#000000', '#000000')
    }
}


document.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action]')
    if (!btn) return

    const actionName = btn.dataset.action
    const handler = actions[actionName]
    if (!handler) return

    e.preventDefault()

    const form = btn.closest('form')
    if (form && btn.type === 'submit' && !form.reportValidity()) {
        return
    }

    const oldHtml = btn.innerHTML

    try {
        btn.disabled = true
        if (btn.type === 'submit') btn.textContent = 'Загрузка...'

        await handler(btn)

    } catch (err) {
        console.error(err)
        TOAST.errorToast('Ошибка', await API.errResolve(err.code))
    } finally {
        btn.disabled = false
        btn.innerHTML = oldHtml
    }
})