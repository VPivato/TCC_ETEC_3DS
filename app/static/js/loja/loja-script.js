new Swiper('.card-wrapper', {
    loop: true,
    spaceBetween: 30,

    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },

    breakpoints: {
        0: {
            slidesPerView: 1.5
        },
        768: {
            slidesPerView: 2.5
        },
        1280: {
            slidesPerView: 4
        },
    }
});