const max_toasts = 5
let activeToasts = []


function createToast(title="Уведомление", msg="сообщение", duration=3000, color='#1e631e', hover='#2edd2e') {
    if (activeToasts.length >= max_toasts) {
        const oldestToast = activeToasts.shift()
        if (oldestToast) {oldestToast.remove()}
        console.log(`[TOAST] Removed toast bc toast overflow`)
    }

    const toast = document.createElement('div')
    toast.className = 'toast'

    const header = document.createElement('h3')
    header.className = 'toast-header'
    header.textContent = title

    const body = document.createElement('p')
    body.className = 'toast-body'
    body.textContent = msg

    toast.appendChild(header)
    toast.appendChild(body)

    toast.style.setProperty('--toast_border', color)
    toast.style.setProperty('--toast_hover', hover)

    document.querySelector('.toast-container').appendChild(toast)

    void toast.offsetHeight

    toast.classList.add('show')

    toast._timer = setTimeout(() => {
        hideToast(toast)
        console.log('[TOAST] Hiding toast')
    }, duration)

    toast.addEventListener('mouseenter', (event) => {
        clearTimeout(toast._timer)
    })

    toast.addEventListener('mouseleave', (event) => {
        clearTimeout(toast._timer)
        toast._timer = setTimeout(() => hideToast(toast), 1000)
    })

    activeToasts.push(toast)

    console.log('[TOASTS] Finished creating toast')
}

function hideToast(toast) {
    if (!toast.classList.contains('show')) return

    toast.classList.remove('show')
    
    setTimeout(() => {
        toast.remove()
        
        const index = activeToasts.indexOf(toast)
        if (index > -1) {
            activeToasts.splice(index, 1)
        }
        console.log(`[TOAST] Removed toast, active toasts: ${activeToasts.length}`)
    }, 500)
}

function warningToast(title='Предупреждение', msg='Сообщение', duration=3000) {
    createToast(title, msg, duration, '#635e1e', '#dadd2e')
}

function errorToast(title='Ошибка', msg='Сообщение', duration=3000) {
    createToast(title, msg, duration, '#631e1e', '#dd2e2e')
}

function infoToast(title='Информация', msg='Сообщение', duration=3000) {
    createToast(title, msg, duration, '#1e6327', '#2edd2e')
}

function clearAllToasts() {
    for (const toast of activeToasts) {
        toast.remove()
    }
}

function hideAllToasts() {
    for (const toast of activeToasts) {
        toast.classList.remove('show')
    }
}

const TOAST = {
    createToast,
    warningToast,
    errorToast,
    infoToast,
    clearAllToasts,
    hideAllToasts,
}

export default TOAST