//Efeito de transição entre Cadastro e Login

const container = document.querySelector('.container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');

registerBtn.addEventListener('click', () => {
    container.classList.add('active');
});

loginBtn.addEventListener('click', () => {
    container.classList.remove('active');
});

//Fazer a o link abrir em outra guia no computador, mas no celular não.

document.getElementById('link').addEventListener('click', function (event) {
    // Verifica se o dispositivo é um celular
    if (/Mobi|Android/i.test(navigator.userAgent)) {
        // Se for celular, não faz nada especial (abre na mesma guia)
    } else {
        // Se for desktop, abre em uma nova guia
        event.preventDefault(); // Previne o comportamento padrão do link
        window.open(this.href, '_blank'); // Abre em nova guia
    }
});
