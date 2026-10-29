<?php
// Portada pública: nombre del proyecto, menú, descripción, registro e ingreso.
// Pensada para buscadores (SEO) y motores con IA (GEO): un único h1, respuesta
// directa a "¿qué es?", preguntas frecuentes y datos estructurados schema.org.
require_once __DIR__ . '/inc/inicio.php';

$usuario = usuarioActual();
$salida = isset($_GET['salida']);

// Las mismas preguntas se muestran en la página y se publican como FAQPage.
$preguntas = [
    ['¿Puedo importar mi inventario desde Excel?',
     'Sí. La pestaña Ingreso de equipos permite cargar equipos en forma masiva desde una planilla de Excel, '
     . 'y el inventario se puede exportar a Excel con los filtros aplicados.'],
    ['¿Por qué mi cuenta figura como pendiente?',
     'Todas las cuentas nuevas quedan pendientes hasta que un administrador aprueba la solicitud. '
     . 'Una vez aprobada, ya podés ingresar con tu usuario y contraseña.'],
    ['¿Qué diferencia hay entre técnico y administrador?',
     'El técnico opera el inventario, el taller, los repuestos y la papelera. El administrador además gestiona '
     . 'usuarios, aprueba registros, responde consultas y realiza las bajas definitivas.'],
    ['¿Se pierde un equipo si lo elimino?',
     'No. Los equipos eliminados van a la papelera, desde donde se pueden restaurar. '
     . 'Solo un administrador puede darlos de baja en forma definitiva.'],
    ['¿Mis datos están protegidos?',
     'Las contraseñas se guardan encriptadas y el acceso a la aplicación requiere una sesión iniciada; '
     . 'sin ella, el sistema redirige a la página de error.'],
];

$url = urlBase();
$jsonld = [
    '@context' => 'https://schema.org',
    '@graph' => [
        [
            '@type' => 'WebApplication',
            '@id' => $url . '#aplicacion',
            'name' => NOMBRE_SISTEMA,
            'alternateName' => NOMBRE_CORTO,
            'url' => $url,
            'description' => DESCRIPCION_SISTEMA,
            'applicationCategory' => 'BusinessApplication',
            'operatingSystem' => 'Web',
            'inLanguage' => 'es-AR',
            'featureList' => [
                'Inventario con buscador, filtros, historial y exportación a Excel',
                'Ingreso de equipos con programación de canales e importación desde Excel',
                'Circuito de reparación en taller',
                'Stock de repuestos por taller',
                'Estadísticas del parque de equipos',
                'Administración de usuarios con dos niveles de acceso',
            ],
            'creator' => ['@id' => $url . '#utn-frh'],
        ],
        [
            '@type' => 'CollegeOrUniversity',
            '@id' => $url . '#utn-frh',
            'name' => 'Universidad Tecnológica Nacional · Facultad Regional Haedo',
            'address' => [
                '@type' => 'PostalAddress',
                'streetAddress' => 'París 532',
                'addressLocality' => 'Haedo',
                'addressRegion' => 'Provincia de Buenos Aires',
                'addressCountry' => 'AR',
            ],
        ],
        [
            '@type' => 'FAQPage',
            'mainEntity' => array_map(fn($p) => [
                '@type' => 'Question',
                'name' => $p[0],
                'acceptedAnswer' => ['@type' => 'Answer', 'text' => $p[1]],
            ], $preguntas),
        ],
    ],
];

encabezado('Inicio', 'inicio', [
    'titulo_completo' => NOMBRE_SISTEMA . ' · Taller y repuestos',
    'jsonld' => $jsonld,
    'ancho_completo' => true,
]);

$icono = fn(string $trazos, int $tam = 22) => '<svg width="' . $tam . '" height="' . $tam . '" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    . 'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $trazos . '</svg>';
$tilde = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
    . 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 5 5 9-10"/></svg>';
$cruz = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
    . 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>';
$flecha = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    . 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

// Trazos de los íconos que se repiten
$iInventario = '<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m3 8 9 5 9-5"/><path d="M12 13v8"/>';
$iIngreso = '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M4 17v3h16v-3"/>';
$iTaller = '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>';
$iRepuestos = '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>';
$iUsuarios = '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M19 8v6M16 11h6"/>';

/**
 * Captura real de la aplicación (con datos de ejemplo) en sus dos versiones: se muestra
 * la del tema activo y la otra no se descarga (loading="lazy" + display:none).
 */
$captura = fn(string $nombre, string $alt) =>
    '<img class="captura solo-claro" src="img/portada/' . $nombre . '-claro.webp" alt="' . e($alt) . '" width="1568" height="744" loading="lazy" decoding="async">'
    . '<img class="captura solo-oscuro" src="img/portada/' . $nombre . '-oscuro.webp" alt="' . e($alt) . '" width="1568" height="744" loading="lazy" decoding="async">';
$circuloFlecha = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
    . 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8 12h8M13 8l4 4-4 4"/></svg>';
?>
<section class="hero" aria-labelledby="titulo-portada">
    <div class="hero-imagen" aria-hidden="true">
        <img src="img/portada/inventario-oscuro.webp" alt="" width="1568" height="744" decoding="async" fetchpriority="high">
    </div>
    <div class="contenedor hero-texto">
        <p class="producto"><img src="img/logo.svg" alt="" width="28" height="28"><?= e(NOMBRE_CORTO) ?></p>
        <h1 id="titulo-portada">Inventario de equipos de radio: del alta al taller, en un solo sistema</h1>
        <p class="hero-bajada">
            El <strong><?= e(NOMBRE_SISTEMA) ?></strong> es una aplicación web para gestionar un parque
            de equipos de radiocomunicación: inventario con programación de canales, circuito de reparación
            en taller, stock de repuestos por taller y estadísticas.
        </p>
        <p class="hero-nota">Captura del sistema con datos de ejemplo · Proyecto Integrador de Programación IV · UTN FRH</p>
        <?php if ($salida): ?>
            <p class="mensaje-info" role="status">Cerraste la sesión correctamente.</p>
        <?php endif; ?>
        <div class="hero-acciones">
            <?php if ($usuario): ?>
                <a class="boton boton-contorno" href="app.php">Ir al sistema <?= $flecha ?></a>
            <?php else: ?>
                <a class="boton boton-contorno" href="registro.php"><?= $icono($iUsuarios, 18) ?> Solicitar acceso</a>
            <?php endif; ?>
        </div>
        <ul class="hero-enlaces">
            <?php if ($usuario): ?>
                <li>Sesión iniciada como <strong><?= e($usuario['username']) ?></strong></li>
            <?php else: ?>
                <li><a href="ingresar.php"><?= $icono('<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/>', 18) ?>Ya tengo cuenta: ingresar</a></li>
            <?php endif; ?>
            <li><a href="contacto.php"><?= $icono('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>', 18) ?>Hacé una consulta</a></li>
        </ul>
    </div>

    <div class="contenedor">
        <section class="panel" aria-labelledby="titulo-roles">
            <h2 id="titulo-roles">Niveles de acceso</h2>
            <div class="opciones">
                <article class="opcion opcion-destacada" aria-labelledby="rol-tecnico">
                    <h3 id="rol-tecnico">Técnico</h3>
                    <p class="opcion-bajada">Opera el día a día del parque de equipos.</p>
                    <ul class="opcion-lista">
                        <li><?= $tilde ?>Ingreso de equipos e Inventario</li>
                        <li><?= $tilde ?>Taller, Repuestos y Estadísticas</li>
                        <li><?= $tilde ?>Papelera: restaurar</li>
                        <li class="no"><?= $cruz ?>Usuarios y consultas</li>
                    </ul>
                    <span class="etiqueta">El más habitual</span>
                </article>
                <article class="opcion" aria-labelledby="rol-admin">
                    <h3 id="rol-admin">Administrador</h3>
                    <p class="opcion-bajada">Todo lo del técnico, más la gestión del sistema.</p>
                    <ul class="opcion-lista">
                        <li><?= $tilde ?>Todo lo del técnico</li>
                        <li><?= $tilde ?>Repuestos, incluidas las bajas</li>
                        <li><?= $tilde ?>Papelera: baja definitiva</li>
                        <li><?= $tilde ?>Usuarios y consultas</li>
                    </ul>
                    <span class="etiqueta etiqueta-azul">Acceso completo</span>
                </article>
                <article class="opcion" aria-labelledby="rol-visitante">
                    <h3 id="rol-visitante">Visitante</h3>
                    <p class="opcion-bajada">Conoce el sistema antes de pedir una cuenta.</p>
                    <ul class="opcion-lista">
                        <li><?= $tilde ?>Portada y Quiénes somos</li>
                        <li><?= $tilde ?>Formulario de contacto</li>
                        <li><?= $tilde ?>Solicitud de cuenta</li>
                        <li class="no"><?= $cruz ?>Acceso a la aplicación</li>
                    </ul>
                </article>
            </div>
            <div class="panel-pie">
                <?php if ($usuario): ?>
                    <p>Ya tenés una sesión iniciada como <strong><?= e($usuario['username']) ?></strong>.</p>
                    <a class="boton boton-claro" href="app.php">Ir al sistema</a>
                <?php else: ?>
                    <p>Las cuentas nuevas quedan <strong>pendientes</strong> hasta que un administrador las aprueba.</p>
                    <a class="boton boton-claro" href="registro.php">Crear cuenta</a>
                <?php endif; ?>
            </div>
        </section>
    </div>
</section>

<nav class="subnav" aria-label="Secciones de la portada">
    <div class="contenedor">
        <ul>
            <li><a href="#que-es">Descripción general</a></li>
            <li><a href="#funciones">Funciones</a></li>
            <li><a href="#caracteristicas">Características</a></li>
            <li><a href="#taller">Circuito de taller</a></li>
            <?php if (!$usuario): ?><li><a href="#acceso">Acceso</a></li><?php endif; ?>
            <li><a href="#preguntas">Preguntas frecuentes</a></li>
        </ul>
    </div>
</nav>

<section id="que-es" class="seccion" aria-labelledby="titulo-que-es">
    <div class="contenedor dividida">
        <div class="revelar">
            <h2 id="titulo-que-es">¿Qué es el <?= e(NOMBRE_SISTEMA) ?>?</h2>
            <p>Es una aplicación web que centraliza el registro de los equipos de radiocomunicación de una
               organización —portátiles, móviles y bases— y reemplaza planillas sueltas por una base de datos
               única. Le da a técnicos y administradores las herramientas para:</p>
            <ul class="lista-destacada">
                <li><strong>Registrar y encontrar</strong> cada equipo con su programación de canales (TX/RX y codificación).</li>
                <li><strong>Seguir las reparaciones</strong> desde el envío al taller hasta el egreso, con los repuestos usados.</li>
                <li><strong>Controlar el stock</strong> de repuestos por taller y ver estadísticas del parque.</li>
            </ul>
            <ul class="enlaces-secundarios">
                <li><a href="#taller"><?= $circuloFlecha ?>Ver cómo funciona el circuito de taller</a></li>
                <li><a href="quienes-somos.php"><?= $circuloFlecha ?>Conocé quiénes somos</a></li>
            </ul>
        </div>
        <figure class="galeria revelar" data-galeria>
            <div class="galeria-principal">
                <img class="captura solo-claro" data-variante="claro" src="img/portada/inventario-claro.webp" alt="Pestaña Inventario del sistema: buscador, filtros y tabla de equipos con su estado" width="1568" height="744" loading="lazy" decoding="async">
                <img class="captura solo-oscuro" data-variante="oscuro" src="img/portada/inventario-oscuro.webp" alt="Pestaña Inventario del sistema: buscador, filtros y tabla de equipos con su estado" width="1568" height="744" loading="lazy" decoding="async">
            </div>
            <!-- Miniaturas: las muestra js/sitio.js (sin JavaScript queda la captura del inventario) -->
            <div class="galeria-miniaturas" hidden>
                <?php foreach ([
                    ['inventario', 'Inventario', 'Pestaña Inventario del sistema: buscador, filtros y tabla de equipos con su estado'],
                    ['repuestos', 'Repuestos', 'Pestaña Repuestos: stock por taller con el estado de cada repuesto'],
                    ['estadisticas', 'Estadísticas', 'Pestaña Estadísticas: totales del parque y gráficos por tipo y modelo de equipo'],
                ] as $i => [$nombre, $titulo, $alt]): ?>
                    <button type="button" data-captura="<?= $nombre ?>" data-alt="<?= e($alt) ?>" data-titulo="<?= e($titulo) ?>" aria-pressed="<?= $i === 0 ? 'true' : 'false' ?>">
                        <?= $captura($nombre, '') ?>
                        <span class="solo-lectores">Ver captura de <?= e($titulo) ?></span>
                    </button>
                <?php endforeach; ?>
            </div>
            <figcaption>Capturas del sistema con datos de ejemplo · <span data-galeria-titulo>Inventario</span></figcaption>
        </figure>
    </div>
</section>

<section id="funciones" class="seccion seccion-gris" aria-labelledby="titulo-funciones">
    <div class="contenedor">
        <div class="carrusel-cabecera">
            <div class="encabezado">
                <h2 id="titulo-funciones">¿Por qué usar <?= e(NOMBRE_CORTO) ?>?</h2>
                <p>Todo el ciclo de vida del equipo en seis módulos, con buscador e historial de cambios.</p>
            </div>
            <!-- Flechas del carrusel: las muestra js/sitio.js -->
            <div class="carrusel-controles" hidden>
                <button type="button" data-carrusel="-1" aria-label="Anterior"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 6-6 6 6 6"/></svg></button>
                <button type="button" data-carrusel="1" aria-label="Siguiente"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></button>
            </div>
        </div>

        <ul class="carrusel" tabindex="0" aria-label="Módulos del sistema">
            <li class="tarjeta-oscura">
                <div class="tarjeta-visual" aria-hidden="true">
                    <div class="captura-recorte"><img class="captura" src="img/portada/inventario-oscuro.webp" alt="" width="1568" height="744" loading="lazy" decoding="async"></div>
                </div>
                <div class="tarjeta-texto">
                    <p class="antetitulo">Inventario</p>
                    <h3>Encontrá cualquier equipo en segundos</h3>
                    <p>Buscador por número de serie, filtros por tipo, marca, modelo, escala, sector y estado, historial y exportación a Excel.</p>
                </div>
            </li>
            <li class="tarjeta-oscura">
                <div class="tarjeta-visual visual-anillos" aria-hidden="true">
                    <span class="nucleo"><?= $icono($iIngreso, 26) ?></span>
                </div>
                <div class="tarjeta-texto">
                    <p class="antetitulo">Ingreso de equipos</p>
                    <h3>Altas con su programación de canales</h3>
                    <p>Frecuencias TX/RX y codificación, imagen del modelo e importación masiva desde Excel.</p>
                </div>
            </li>
            <li class="tarjeta-oscura">
                <div class="tarjeta-visual visual-estados" aria-hidden="true">
                    <span class="pildora pildora-ambar">En diagnóstico</span>
                    <span class="pildora pildora-azul">En reparación</span>
                    <span class="pildora pildora-verde">Egresado</span>
                </div>
                <div class="tarjeta-texto">
                    <p class="antetitulo">Taller</p>
                    <h3>Cada reparación, paso por paso</h3>
                    <p>Envío, recepción, ingreso y egreso registrando los repuestos utilizados.</p>
                </div>
            </li>
            <li class="tarjeta-oscura">
                <div class="tarjeta-visual visual-lista" aria-hidden="true">
                    <span><b>Antena VHF Alta</b><i class="pildora pildora-ambar">Stock bajo</i></span>
                    <span><b>Batería 2200 mAh</b><i class="pildora pildora-verde">OK</i></span>
                    <span><b>Clip de cinturón</b><i class="pildora pildora-verde">OK</i></span>
                </div>
                <div class="tarjeta-texto">
                    <p class="antetitulo">Repuestos</p>
                    <h3>Stock por taller, con aviso de faltantes</h3>
                    <p>Ingresos, ajustes, consumo en reparaciones y bajas del catálogo de repuestos.</p>
                </div>
            </li>
            <li class="tarjeta-oscura">
                <div class="tarjeta-visual visual-barras" aria-hidden="true">
                    <span class="b1"></span><span class="b2"></span>
                    <span class="b3 activa"><em>Excel</em></span>
                    <span class="b4"></span><span class="b5"></span>
                </div>
                <div class="tarjeta-texto">
                    <p class="antetitulo">Estadísticas</p>
                    <h3>El estado del parque, de un vistazo</h3>
                    <p>Distribución por tipo y modelo, incidencias de taller y consumo de repuestos.</p>
                </div>
            </li>
            <li class="tarjeta-oscura">
                <div class="tarjeta-visual visual-etiquetas" aria-hidden="true">
                    <span class="etiquetas">#técnico #administrador #aprobación #consultas #claves #usuarios #registro #roles #técnico #administrador</span>
                    <span class="nucleo"><?= $icono($iUsuarios, 26) ?></span>
                </div>
                <div class="tarjeta-texto">
                    <p class="antetitulo">Administración</p>
                    <h3>Usuarios, aprobaciones y consultas</h3>
                    <p>Aprobación de registros, reseteo de claves y respuesta a las consultas del formulario de contacto.</p>
                </div>
            </li>
        </ul>
    </div>
</section>

<section id="caracteristicas" class="seccion" aria-labelledby="titulo-caracteristicas">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Características</p>
            <h2 id="titulo-caracteristicas">Pensado para el trabajo diario del taller</h2>
            <p>Dos niveles de acceso, historial de cada cambio y una papelera para no perder nada por error.</p>
        </div>
        <dl class="grilla-lineas revelar">
            <div>
                <?= $icono('<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M16 3.1a4 4 0 0 1 0 7.8M22 21a7 7 0 0 0-4-6.3"/>', 36) ?>
                <dt>Para quién</dt><dd>Técnicos de radiocomunicaciones y administradores del parque de equipos.</dd>
            </div>
            <div>
                <?= $icono('<path d="M5 12a7 7 0 0 1 14 0"/><path d="M8.5 12a3.5 3.5 0 0 1 7 0"/><circle cx="12" cy="12" r="1"/><path d="M12 13v8"/>', 36) ?>
                <dt>Qué gestiona</dt><dd>Equipos, canales (TX/RX y codificación), reparaciones, repuestos por taller y usuarios.</dd>
            </div>
            <div>
                <?= $icono('<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>', 36) ?>
                <dt>Acceso</dt><dd>Registro con aprobación de un administrador; ingreso con usuario y contraseña.</dd>
            </div>
            <div>
                <?= $icono('<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>', 36) ?>
                <dt>Historial completo</dt><dd>Cada alta, modificación, envío a taller y baja queda registrada en el historial del equipo.</dd>
            </div>
            <div>
                <?= $icono('<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/>', 36) ?>
                <dt>Papelera segura</dt><dd>Los equipos eliminados se pueden restaurar; solo un administrador los da de baja definitiva.</dd>
            </div>
            <div>
                <?= $icono('<path d="m8 9-4 3 4 3M16 9l4 3-4 3M14 5l-4 14"/>', 36) ?>
                <dt>Tecnologías</dt><dd>HTML5, CSS, JavaScript, PHP 8 y MySQL/MariaDB.</dd>
            </div>
        </dl>
    </div>
</section>

<section id="taller" class="seccion seccion-gris" aria-labelledby="titulo-taller">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Circuito de taller</p>
            <h2 id="titulo-taller">Cada reparación queda registrada, paso por paso</h2>
            <p>El equipo cambia de estado en el inventario a medida que avanza, y los repuestos usados se
               descuentan del stock del taller que lo reparó.</p>
        </div>
        <div class="circuito revelar">
            <ol class="flujo">
                <li><span class="nodo"><?= $icono('<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>') ?></span><h3>Envío</h3><p>Desde el inventario se envía el equipo al taller indicando la falla.</p></li>
                <li><span class="nodo"><?= $icono('<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m8 12 3 3 5-6"/>') ?></span><h3>Recepción</h3><p>El taller confirma que recibió el equipo y queda a su cargo.</p></li>
                <li><span class="nodo"><?= $icono($iTaller) ?></span><h3>Reparación</h3><p>Se registra el ingreso con los elementos recibidos y cada paso queda en el historial del equipo.</p></li>
                <li><span class="nodo"><?= $icono('<path d="M20 6 9 17l-5-5"/>') ?></span><h3>Egreso</h3><p>Se registra la salida con los repuestos utilizados y el equipo vuelve al servicio.</p></li>
            </ol>
        </div>
        <div class="dos-capturas revelar">
            <figure>
                <div class="marco"><?= $captura('repuestos', 'Pestaña Repuestos: stock por taller con el estado de cada repuesto') ?></div>
                <figcaption>Repuestos por taller, con aviso de stock bajo.</figcaption>
            </figure>
            <figure>
                <div class="marco"><?= $captura('estadisticas', 'Pestaña Estadísticas: totales del parque y gráficos por tipo y modelo de equipo') ?></div>
                <figcaption>Estadísticas del parque y de las reparaciones.</figcaption>
            </figure>
        </div>
    </div>
</section>

<?php if (!$usuario): ?>
<section id="acceso" class="seccion" aria-labelledby="titulo-acceso">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Acceso</p>
            <h2 id="titulo-acceso">¿Cómo obtengo acceso?</h2>
            <p>Tres pasos y estás adentro. Las cuentas nuevas las aprueba un administrador.</p>
        </div>
        <ol class="pasos-acceso grilla-lineas revelar">
            <li><span class="paso-numero">01</span><h3>Registrate</h3><p>Completá el <a href="registro.php">formulario de registro</a> con tu nombre, email y una contraseña.</p></li>
            <li><span class="paso-numero">02</span><h3>Esperá la aprobación</h3><p>Un administrador revisa la solicitud; hasta entonces la cuenta queda pendiente.</p></li>
            <li><span class="paso-numero">03</span><h3>Ingresá</h3><p><a href="ingresar.php">Iniciá sesión</a> con tu usuario y contraseña y accedé al sistema.</p></li>
        </ol>
    </div>
</section>
<?php endif; ?>

<section id="preguntas" class="seccion<?= $usuario ? '' : ' seccion-gris' ?>" aria-labelledby="titulo-preguntas">
    <div class="contenedor">
        <div class="encabezado revelar">
            <h2 id="titulo-preguntas">Preguntas frecuentes</h2>
            <p>¿No encontrás tu respuesta? Escribinos desde la página de <a href="contacto.php">contacto</a>.</p>
        </div>
        <div class="preguntas revelar">
            <?php foreach ($preguntas as $i => [$pregunta, $respuesta]): ?>
                <details<?= $i === 0 ? ' open' : '' ?>>
                    <summary><?= e($pregunta) ?><span class="mas" aria-hidden="true"></span></summary>
                    <p><?= e($respuesta) ?></p>
                </details>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<?php if (!$usuario): ?>
<section class="seccion seccion-final" aria-labelledby="titulo-final">
    <div class="contenedor">
        <div class="llamado revelar">
            <h2 id="titulo-final">Empezá a ordenar tu parque de equipos</h2>
            <p>Creá tu cuenta y un administrador la habilitará.</p>
            <div class="hero-acciones">
                <a class="boton boton-primario" href="registro.php">Crear cuenta <?= $flecha ?></a>
                <a class="boton boton-secundario" href="contacto.php">Hacer una consulta</a>
            </div>
        </div>
    </div>
</section>
<?php endif; ?>
<?php
pie();
