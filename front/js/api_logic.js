import ERRORS from './errors.js'

async function _request(method, endpoint, body = null) {
    const options = { method: method, credentials: 'include' }  // Сборка настроек
    if (body !== null) {
        options.headers = { 'Content-Type': 'application/json' } // добавить заголовок
        options.body = JSON.stringify(body) // добвить тело
    }

    let response
    try {
        response = await fetch(endpoint, options) // отправить запрос
    }
    catch (err) {
        console.error(`[API] Error awaiting response: ${err}`)
        return { status: 'error', code: 'connection.no' }
    }

    if (response.status === 401) { // если токен просрочен
        if (response.status === 401 && !endpoint.includes('login')) {window.location.href = '/app/login'}
        return { status: 'error', code: 'session.expired' }
    }

    const contentType = response.headers.get("content-type")
    if (!contentType || !contentType.includes("application/json")) {
        console.error(`[API] Non-JSON response: ${response.status}`)
        return { status: 'error', code: 'server.error' }
    }

    let data
    try {
        data = await response.json() // распаковать json
    }
    catch (err) {
        console.error(`[API] Error during unpacking data: ${err}`)
        return { status: 'error', code: 'server.error' }
    }

        if (!response.ok && data.status !== 'error') {
        return { status: 'error', code: data.code || data.detail || 'server.error' }
    }

    return data
}

async function deposit(amount, acc_num) {
    return await _request('POST', "/api/accounts/deposit", { amount: amount, acc_num: acc_num })
}

async function login(login, pin) {
    return await _request('POST', "/api/login", { login: login, pin: pin })
}

async function errResolve(error) {
    let text
    try {
        text = ERRORS[error]
    }
    catch (err) {
        console.error(`[ERR RESOLVE] Cant resolve error code: ${err}`)
        text = error
    }
    return text
}
const API = {
    deposit,
    login,
    errResolve,
}
export default API