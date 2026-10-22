// Páginas públicas: botón de modo claro/oscuro y aparición suave de las secciones.
// El tema inicial lo pone js/tema.js; la elección se comparte con la aplicación (misma clave).

const raiz = document.documentElement;
const botonTema = document.querySelector('.sitio-cabecera .btn-tema');

if (botonTema) {
    const marcar = () => botonTema.setAttribute('aria-pressed', String(raiz.dataset.tema === 'oscuro'));
    botonTema.hidden = false;
    marcar();
    botonTema.addEventListener('click', () => {
        const tema = raiz.dataset.tema === 'oscuro' ? 'claro' : 'oscuro';
        raiz.dataset.tema = tema;
        marcar();
        try {
            localStorage.setItem('tema', tema);
        } catch {
            // sin almacenamiento: la elección dura hasta recargar
        }
    });
}

// Aparición al desplazarse. Solo se ocultan los bloques que todavía están debajo
// de la pantalla, así lo visible al cargar nunca parpadea. Sin JavaScript, o con
// "reducir movimiento", todo se ve desde el principio.
const bloques = [...document.querySelectorAll('.revelar')];
const sinMovimiento = matchMedia('(prefers-reduced-motion: reduce)').matches;

if (bloques.length && 'IntersectionObserver' in window && !sinMovimiento) {
    const observador = new IntersectionObserver((entradas) => {
        for (const entrada of entradas) {
            if (entrada.isIntersecting) {
                entrada.target.classList.remove('revelar-pendiente');
                observador.unobserve(entrada.target);
            }
        }
    }, { rootMargin: '0px 0px -8% 0px' });

    for (const bloque of bloques) {
        if (bloque.getBoundingClientRect().top > innerHeight) {
            bloque.classList.add('revelar-pendiente');
            observador.observe(bloque);
        }
    }
}
