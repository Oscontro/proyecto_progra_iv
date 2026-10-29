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

// Mostrar/ocultar la contraseña en los formularios de ingreso y registro.
for (const boton of document.querySelectorAll('.ver-clave')) {
    const campo = document.getElementById(boton.getAttribute('aria-controls'));
    if (!campo) continue;
    boton.hidden = false;
    boton.addEventListener('click', () => {
        const ver = campo.type === 'password';
        campo.type = ver ? 'text' : 'password';
        boton.textContent = ver ? 'Ocultar' : 'Mostrar';
        boton.setAttribute('aria-pressed', String(ver));
        campo.focus();
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

// Botón "volver arriba": aparece después de bajar una pantalla.
const volverArriba = document.querySelector('.volver-arriba');
if (volverArriba) {
    let pendienteVolver = false;
    const mostrarVolver = () => {
        pendienteVolver = false;
        volverArriba.classList.toggle('visible', scrollY > innerHeight * 0.8);
    };
    volverArriba.hidden = false;
    volverArriba.addEventListener('click', () => {
        scrollTo({ top: 0, behavior: sinMovimiento ? 'auto' : 'smooth' });
        // El foco vuelve al principio de la página (útil con teclado y lectores de pantalla).
        document.querySelector('.sitio-marca')?.focus({ preventScroll: true });
    });
    addEventListener('scroll', () => {
        if (!pendienteVolver) {
            pendienteVolver = true;
            requestAnimationFrame(mostrarVolver);
        }
    }, { passive: true });
    mostrarVolver();
}

// Galería de la portada: las miniaturas cambian la captura grande (en sus dos
// versiones, clara y oscura, para que siga al tema).
for (const galeria of document.querySelectorAll('[data-galeria]')) {
    const miniaturas = galeria.querySelector('.galeria-miniaturas');
    const principales = galeria.querySelectorAll('.galeria-principal img');
    const titulo = galeria.querySelector('[data-galeria-titulo]');
    miniaturas.hidden = false;
    miniaturas.addEventListener('click', (evento) => {
        const boton = evento.target.closest('button[data-captura]');
        if (!boton) return;
        for (const img of principales) {
            img.src = `img/portada/${boton.dataset.captura}-${img.dataset.variante}.webp`;
            img.alt = boton.dataset.alt;
        }
        titulo.textContent = boton.dataset.titulo;
        for (const otro of miniaturas.querySelectorAll('button')) {
            otro.setAttribute('aria-pressed', String(otro === boton));
        }
    });
}

// Carrusel de funciones: las flechas avanzan de a una tarjeta y se apagan en los extremos.
const carrusel = document.querySelector('.carrusel');
const controles = document.querySelector('.carrusel-controles');
if (carrusel && controles) {
    const [anterior, siguiente] = controles.querySelectorAll('button');
    const actualizar = () => {
        anterior.disabled = carrusel.scrollLeft <= 1;
        siguiente.disabled = carrusel.scrollLeft + carrusel.clientWidth >= carrusel.scrollWidth - 1;
    };
    controles.hidden = false;
    controles.addEventListener('click', (evento) => {
        const boton = evento.target.closest('button[data-carrusel]');
        if (!boton) return;
        const paso = carrusel.firstElementChild.getBoundingClientRect().width + parseFloat(getComputedStyle(carrusel).columnGap);
        carrusel.scrollBy({ left: Number(boton.dataset.carrusel) * paso, behavior: sinMovimiento ? 'auto' : 'smooth' });
    });
    carrusel.addEventListener('scroll', actualizar, { passive: true });
    addEventListener('resize', actualizar);
    actualizar();
}

// Barra de secciones: marca la sección que se está leyendo (la última cuyo
// comienzo ya pasó por debajo de la cabecera y la barra).
const subnav = document.querySelector('.subnav');
if (subnav) {
    const enlaces = [...subnav.querySelectorAll('a[href^="#"]')]
        .map((a) => ({ a, seccion: document.getElementById(a.hash.slice(1)) }))
        .filter((x) => x.seccion);
    let pendiente = false;
    const marcar = () => {
        pendiente = false;
        const limite = subnav.getBoundingClientRect().bottom + 24;
        let actual = null;
        for (const x of enlaces) {
            if (x.seccion.getBoundingClientRect().top <= limite) actual = x;
        }
        for (const x of enlaces) {
            if (x === actual) {
                x.a.setAttribute('aria-current', 'true');
                // Mantiene visible el enlace activo cuando la barra se desplaza (celulares).
                const ul = x.a.closest('ul');
                const izq = x.a.offsetLeft - ul.offsetLeft;
                if (izq < ul.scrollLeft || izq + x.a.offsetWidth > ul.scrollLeft + ul.clientWidth) ul.scrollLeft = izq - 16;
            } else {
                x.a.removeAttribute('aria-current');
            }
        }
    };
    addEventListener('scroll', () => {
        if (!pendiente) {
            pendiente = true;
            requestAnimationFrame(marcar);
        }
    }, { passive: true });
    marcar();
}
