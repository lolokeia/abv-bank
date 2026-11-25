
function getRandomElement(arr) {
  const randomIndex = Math.floor(Math.random() * arr.length);
  return arr[randomIndex];
}

spl_main = ["Иллюзия безопасности", "В моем гелике", "В моей сумке", "На моей яхте", "Точно не пирамида", "Пузырь не лопнет!", "АБВ-БАНК ltd"]

function SplashMain() {
    const Element = document.getElementById("splash")
    Element.textContent = '(' + getRandomElement(spl_main) + ')'
}

spl_err = ["Ваши данные уже горят", "Ваши деньги уже горят", "АБВ банк вернет вам 100р (не факт)", "Бедняга прилег", "Сервер горит", "Сентябрь горит", "Чутка ошибка", "1 / 0 =?"]
function SplashErr() {
    const Element = document.getElementById("splash")
    Element.textContent = '(' + getRandomElement(spl_err) + ')'
}