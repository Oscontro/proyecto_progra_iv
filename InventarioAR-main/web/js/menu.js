// Menú hamburguesa de las páginas públicas (en pantallas angostas).
// Sin JavaScript el botón queda oculto y el menú se ve completo.

const cabecera = document.querySelector('.sitio-cabecera');
const boton = cabecera?.querySelector('.menu-boton');
const menu = document.getElementById('menu-principal');

if (cabecera && boton && menu) {
    cabecera.classList.add('con-menu');
    boton.hidden = false;

    const abrir = (abierto) => {
        boton.setAttribute('aria-expanded', String(abierto));
        cabecera.classList.toggle('menu-abierto', abierto);
    };

    boton.addEventListener('click', () => abrir(boton.getAttribute('aria-expanded') !== 'true'));

    // Escape cierra y devuelve el foco al botón.
    document.addEventListener('keydown', (evento) => {
        if (evento.key === 'Escape' && cabecera.classList.contains('menu-abierto')) {
            abrir(false);
            boton.focus();
        }
    });

    // Un enlace interno (#funciones, #preguntas…) cierra el menú al navegar.
    menu.addEventListener('click', (evento) => {
        if (evento.target.closest('a')) abrir(false);
    });

    // Al pasar a pantalla ancha el menú vuelve a su estado normal.
    matchMedia('(min-width: 761px)').addEventListener('change', (consulta) => {
        if (consulta.matches) abrir(false);
    });
}
