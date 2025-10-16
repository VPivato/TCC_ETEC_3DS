document.getElementById('btn-sobre').addEventListener('click', () => {
    window.location.href = '/info/sobre'
})

if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}