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
?>
<section class="hero" aria-labelledby="titulo-portada">
    <div class="hero-fondo" aria-hidden="true"><span class="haz"></span></div>
    <div class="contenedor hero-texto">
        <p class="insignia"><span class="punto" aria-hidden="true"></span>Proyecto Integrador · UTN FRH <span class="insignia-etiqueta">Programación IV</span></p>
        <h1 id="titulo-portada" class="degradado">Inventario de equipos de radio, del alta al taller</h1>
        <p class="hero-bajada">
            El <strong><?= e(NOMBRE_SISTEMA) ?></strong> es una aplicación web para gestionar un parque
            de equipos de radiocomunicación: inventario con programación de canales, circuito de reparación
            en taller, stock de repuestos por taller y estadísticas, en un solo lugar.
        </p>
        <?php if ($salida): ?>
            <p class="mensaje-info" role="status">Cerraste la sesión correctamente.</p>
        <?php endif; ?>
        <div class="hero-acciones">
            <?php if ($usuario): ?>
                <a class="boton boton-primario" href="app.php">Ir al sistema <?= $flecha ?></a>
                <span class="texto-suave">Sesión iniciada como <strong><?= e($usuario['username']) ?></strong></span>
            <?php else: ?>
                <a class="boton boton-primario" href="registro.php">Solicitar acceso</a>
                <a class="boton boton-secundario" href="#taller">Cómo funciona</a>
            <?php endif; ?>
        </div>
    </div>

    <figure class="contenedor hero-captura">
        <div class="dispositivo">
            <?= $captura('inventario', 'Pestaña Inventario del sistema: buscador, filtros y tabla de equipos con su estado') ?>
        </div>
        <figcaption class="solo-lectores">Captura de la pestaña Inventario con datos de ejemplo.</figcaption>
    </figure>
</section>

<section class="franja" aria-labelledby="titulo-franja">
    <h2 id="titulo-franja" class="franja-titulo">Hecho con tecnologías web estándar</h2>
    <div class="cinta">
        <!-- La lista va dos veces para que el desplazamiento sea continuo; la copia se oculta a los lectores -->
        <ul class="cinta-pista">
            <li>HTML5</li><li>CSS</li><li>JavaScript</li><li>PHP 8</li><li>MySQL</li><li>MariaDB</li><li>Excel</li><li>Resend</li>
        </ul>
        <ul class="cinta-pista" aria-hidden="true">
            <li>HTML5</li><li>CSS</li><li>JavaScript</li><li>PHP 8</li><li>MySQL</li><li>MariaDB</li><li>Excel</li><li>Resend</li>
        </ul>
    </div>
</section>

<section id="funciones" class="seccion" aria-labelledby="titulo-funciones">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Funciones</p>
            <h2 id="titulo-funciones" class="degradado">Todo el ciclo de vida del equipo, en seis módulos</h2>
            <p>Del ingreso a la baja: cada equipo, cada reparación y cada repuesto quedan registrados en una base
               de datos única, con buscador e historial de cambios.</p>
        </div>

        <ul class="bento">
            <li class="bento-tarjeta bento-ancha revelar">
                <div class="bento-visual visual-captura" aria-hidden="true">
                    <div class="captura-recorte"><?= $captura('inventario', '') ?></div>
                </div>
                <div class="bento-texto">
                    <h3>Inventario</h3>
                    <p>Buscador por número de serie, filtros por tipo, marca, modelo, escala, sector y estado, historial de cada equipo y exportación a Excel.</p>
                </div>
            </li>
            <li class="bento-tarjeta revelar">
                <div class="bento-visual visual-barras" aria-hidden="true">
                    <span class="b1"></span><span class="b2"></span>
                    <span class="b3 activa"><em>Excel</em></span>
                    <span class="b4"></span><span class="b5"></span>
                </div>
                <div class="bento-texto">
                    <h3>Estadísticas</h3>
                    <p>Resumen del parque, distribución por tipo y modelo, incidencias de taller y consumo de repuestos.</p>
                </div>
            </li>
            <li class="bento-tarjeta revelar">
                <div class="bento-visual visual-anillos" aria-hidden="true">
                    <span class="nucleo"><?= $icono($iIngreso, 26) ?></span>
                </div>
                <div class="bento-texto">
                    <h3>Ingreso de equipos</h3>
                    <p>Alta con programación de canales (frecuencias TX/RX y codificación), imagen del modelo e importación masiva desde Excel.</p>
                </div>
            </li>
            <li class="bento-tarjeta revelar">
                <div class="bento-visual visual-estados" aria-hidden="true">
                    <span class="pildora pildora-ambar">En diagnóstico</span>
                    <span class="pildora pildora-azul">En reparación</span>
                    <span class="pildora pildora-verde">Egresado</span>
                </div>
                <div class="bento-texto">
                    <h3>Taller</h3>
                    <p>Circuito completo de reparación: envío, recepción, cambios de estado y egreso registrando los repuestos utilizados.</p>
                </div>
            </li>
            <li class="bento-tarjeta revelar">
                <div class="bento-visual visual-lista" aria-hidden="true">
                    <span><b>Antena VHF Alta</b><i class="pildora pildora-ambar">Stock bajo</i></span>
                    <span><b>Batería 2200 mAh</b><i class="pildora pildora-verde">OK</i></span>
                    <span><b>Clip de cinturón</b><i class="pildora pildora-verde">OK</i></span>
                </div>
                <div class="bento-texto">
                    <h3>Repuestos</h3>
                    <p>Catálogo de repuestos con stock por taller: ingresos, ajustes, consumo en reparaciones y bajas.</p>
                </div>
            </li>
            <li class="bento-tarjeta bento-completa revelar">
                <div class="bento-visual visual-etiquetas" aria-hidden="true">
                    <span class="etiquetas">#técnico #administrador #aprobación #consultas #claves #usuarios #registro #roles #técnico #administrador #aprobación #consultas</span>
                    <span class="nucleo"><?= $icono($iUsuarios, 26) ?></span>
                </div>
                <div class="bento-texto">
                    <h3>Administración</h3>
                    <p>Gestión de usuarios, aprobación de registros, reseteo de claves y respuesta a las consultas del formulario de contacto.</p>
                </div>
            </li>
        </ul>
    </div>
</section>

<section class="seccion" aria-labelledby="titulo-que-es">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">En pocas palabras</p>
            <h2 id="titulo-que-es" class="degradado">¿Qué es el <?= e(NOMBRE_SISTEMA) ?>?</h2>
            <p>Es una aplicación web que centraliza el registro de los equipos de radiocomunicación de una
               organización —portátiles, móviles y bases— junto con su programación de canales, su paso por el
               taller de reparación y los repuestos consumidos. Reemplaza planillas sueltas por una base de datos
               única con buscador, historial de cambios y dos niveles de acceso.</p>
        </div>
        <dl class="grilla-lineas revelar">
            <div>
                <?= $icono('<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="M16 3.1a4 4 0 0 1 0 7.8M22 21a7 7 0 0 0-4-6.3"/>', 28) ?>
                <dt>Para quién</dt><dd>Técnicos de radiocomunicaciones y administradores del parque de equipos.</dd>
            </div>
            <div>
                <?= $icono('<path d="M5 12a7 7 0 0 1 14 0"/><path d="M8.5 12a3.5 3.5 0 0 1 7 0"/><circle cx="12" cy="12" r="1"/><path d="M12 13v8"/>', 28) ?>
                <dt>Qué gestiona</dt><dd>Equipos, canales (TX/RX y codificación), reparaciones, repuestos por taller y usuarios.</dd>
            </div>
            <div>
                <?= $icono('<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>', 28) ?>
                <dt>Acceso</dt><dd>Registro con aprobación de un administrador; ingreso con usuario y contraseña.</dd>
            </div>
            <div>
                <?= $icono('<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>', 28) ?>
                <dt>Historial completo</dt><dd>Cada alta, modificación, envío a taller y baja queda registrada en el historial del equipo.</dd>
            </div>
            <div>
                <?= $icono('<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/>', 28) ?>
                <dt>Papelera segura</dt><dd>Los equipos eliminados se pueden restaurar; solo un administrador los da de baja definitiva.</dd>
            </div>
            <div>
                <?= $icono('<path d="m8 9-4 3 4 3M16 9l4 3-4 3M14 5l-4 14"/>', 28) ?>
                <dt>Tecnologías</dt><dd>HTML5, CSS, JavaScript, PHP 8 y MySQL/MariaDB.</dd>
            </div>
        </dl>
    </div>
</section>

<section id="taller" class="seccion" aria-labelledby="titulo-taller">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Circuito de taller</p>
            <h2 id="titulo-taller" class="degradado">Cada reparación queda registrada, paso por paso</h2>
            <p>El equipo cambia de estado en el inventario a medida que avanza, y los repuestos usados se
               descuentan del stock del taller que lo reparó.</p>
        </div>
        <div class="circuito revelar">
            <div class="circuito-puntos" aria-hidden="true"></div>
            <ol class="flujo">
                <li><span class="nodo"><?= $icono('<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>') ?></span><h3>Envío</h3><p>Desde el inventario se envía el equipo al taller indicando la falla.</p></li>
                <li><span class="nodo"><?= $icono('<path d="M21 8 12 3 3 8v8l9 5 9-5z"/><path d="m8 12 3 3 5-6"/>') ?></span><h3>Recepción</h3><p>El taller confirma que recibió el equipo y queda a su cargo.</p></li>
                <li><span class="nodo"><?= $icono($iTaller) ?></span><h3>Reparación</h3><p>Los cambios de estado quedan en el historial del equipo.</p></li>
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

<section class="seccion" aria-labelledby="titulo-roles">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Roles</p>
            <h2 id="titulo-roles" class="degradado">Dos niveles de acceso, según tu tarea</h2>
            <p>Los técnicos operan el inventario y el taller; los administradores, además, gestionan usuarios y
               realizan las bajas definitivas.</p>
        </div>
        <div class="planes">
            <article class="plan revelar" aria-labelledby="plan-tecnico">
                <h3 id="plan-tecnico">Técnico</h3>
                <p class="plan-bajada">Opera el día a día del parque de equipos.</p>
                <ul class="plan-lista">
                    <li><?= $tilde ?>Ingreso de equipos e Inventario</li>
                    <li><?= $tilde ?>Taller y Estadísticas</li>
                    <li><?= $tilde ?>Repuestos</li>
                    <li><?= $tilde ?>Papelera: restaurar</li>
                    <li class="no"><?= $cruz ?>Usuarios y consultas</li>
                </ul>
            </article>
            <article class="plan plan-destacado revelar" aria-labelledby="plan-admin">
                <p class="plan-cinta">Acceso completo</p>
                <h3 id="plan-admin">Administrador</h3>
                <p class="plan-bajada">Todo lo del técnico, más la gestión del sistema.</p>
                <ul class="plan-lista">
                    <li><?= $tilde ?>Ingreso de equipos e Inventario</li>
                    <li><?= $tilde ?>Taller y Estadísticas</li>
                    <li><?= $tilde ?>Repuestos, incluidas las bajas</li>
                    <li><?= $tilde ?>Papelera: restaurar y baja definitiva</li>
                    <li><?= $tilde ?>Usuarios y consultas</li>
                </ul>
            </article>
        </div>
    </div>
</section>

<?php if (!$usuario): ?>
<section id="acceso" class="seccion" aria-labelledby="titulo-acceso">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Acceso</p>
            <h2 id="titulo-acceso" class="degradado">¿Cómo obtengo acceso?</h2>
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

<section id="preguntas" class="seccion" aria-labelledby="titulo-preguntas">
    <div class="contenedor contenedor-angosto">
        <div class="encabezado revelar">
            <p class="pastilla">Preguntas frecuentes</p>
            <h2 id="titulo-preguntas" class="degradado">Lo que suelen preguntarnos</h2>
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
            <div class="llamado-anillos" aria-hidden="true"></div>
            <h2 id="titulo-final" class="degradado">Empezá a ordenar tu parque de equipos</h2>
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
