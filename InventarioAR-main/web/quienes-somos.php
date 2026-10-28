<?php
// Quiénes somos: origen del proyecto, objetivos, cómo se construyó y contexto académico.
require_once __DIR__ . '/inc/inicio.php';

$usuario = usuarioActual();

$url = urlBase();
$jsonld = [
    '@context' => 'https://schema.org',
    '@type' => 'AboutPage',
    'name' => 'Quiénes somos · ' . NOMBRE_SISTEMA,
    'url' => $url . 'quienes-somos.php',
    'inLanguage' => 'es-AR',
    'about' => [
        '@type' => 'WebApplication',
        'name' => NOMBRE_SISTEMA,
        'alternateName' => NOMBRE_CORTO,
        'url' => $url,
    ],
    'publisher' => [
        '@type' => 'CollegeOrUniversity',
        'name' => 'Universidad Tecnológica Nacional · Facultad Regional Haedo',
    ],
];

encabezado('Quiénes somos', 'quienes', [
    'descripcion' => 'Quiénes somos: el ' . NOMBRE_SISTEMA . ' es el Proyecto Integrador de Programación IV '
        . 'de la UTN Facultad Regional Haedo. Origen, objetivos y cómo se construyó.',
    'jsonld' => $jsonld,
    'ancho_completo' => true,
]);

$icono = fn(string $trazos, int $tam = 22) => '<svg width="' . $tam . '" height="' . $tam . '" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    . 'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' . $trazos . '</svg>';
$flecha = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    . 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
?>
<section class="hero hero-corto" aria-labelledby="titulo-quienes">
    <div class="hero-fondo" aria-hidden="true"><span class="haz"></span></div>
    <div class="contenedor hero-texto">
        <p class="insignia"><span class="punto" aria-hidden="true"></span>Proyecto Integrador · UTN FRH <span class="insignia-etiqueta">Programación IV</span></p>
        <h1 id="titulo-quienes" class="degradado">Quiénes somos</h1>
        <p class="hero-bajada">
            Somos estudiantes de la <strong>Universidad Tecnológica Nacional, Facultad Regional Haedo</strong>.
            <?= e(NOMBRE_CORTO) ?> nació como el Proyecto Integrador de Programación IV: llevar a la web una
            herramienta real para ordenar el parque de equipos de radio de un taller de radiocomunicaciones.
        </p>
    </div>
</section>

<section class="seccion" aria-labelledby="titulo-proyecto">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">El proyecto</p>
            <h2 id="titulo-proyecto" class="degradado">Un problema concreto, resuelto con software</h2>
            <p>En un taller de radiocomunicaciones, saber dónde está cada equipo, qué canales tiene programados,
               cuántas veces pasó por reparación y qué repuestos quedan suele depender de planillas sueltas.
               Quisimos reunir toda esa información en un solo sistema, accesible desde el navegador.</p>
        </div>
        <dl class="grilla-lineas revelar">
            <div>
                <?= $icono('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>', 28) ?>
                <dt>Misión</dt><dd>Dar trazabilidad completa a cada equipo de radio, desde el alta hasta la baja definitiva.</dd>
            </div>
            <div>
                <?= $icono('<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>', 28) ?>
                <dt>Visión</dt><dd>Una herramienta simple que cualquier técnico pueda usar sin capacitación previa.</dd>
            </div>
            <div>
                <?= $icono('<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/>', 28) ?>
                <dt>Contexto académico</dt><dd>Proyecto Integrador de la materia Programación IV, UTN Facultad Regional Haedo.</dd>
            </div>
        </dl>
    </div>
</section>

<section class="seccion" aria-labelledby="titulo-recorrido">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Nuestro recorrido</p>
            <h2 id="titulo-recorrido" class="degradado">De la aplicación de escritorio a la web</h2>
            <p>El sistema empezó como un programa de escritorio y fue creciendo hasta convertirse en la
               aplicación web que hoy está publicada.</p>
        </div>
        <div class="circuito revelar">
            <div class="circuito-puntos" aria-hidden="true"></div>
            <ol class="flujo">
                <li><span class="nodo"><?= $icono('<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>') ?></span><h3>Escritorio</h3><p>Una primera versión en Python con pestañas para inventario, taller y repuestos.</p></li>
                <li><span class="nodo"><?= $icono('<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>') ?></span><h3>Base de datos</h3><p>Todo el parque de equipos se unificó en una base MySQL/MariaDB.</p></li>
                <li><span class="nodo"><?= $icono('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>') ?></span><h3>Migración web</h3><p>Rehicimos la interfaz con PHP, HTML, CSS y JavaScript, con usuarios y roles.</p></li>
                <li><span class="nodo"><?= $icono('<path d="M4 14a8 8 0 0 1 16 0"/><path d="M12 14V4"/><path d="m8 8 4-4 4 4"/><path d="M3 20h18"/>') ?></span><h3>Publicación</h3><p>El sistema quedó publicado en un hosting, accesible desde cualquier navegador.</p></li>
            </ol>
        </div>
    </div>
</section>

<section class="seccion" aria-labelledby="titulo-valores">
    <div class="contenedor">
        <div class="encabezado revelar">
            <p class="pastilla">Lo que nos guía</p>
            <h2 id="titulo-valores" class="degradado">Principios con los que lo construimos</h2>
        </div>
        <dl class="grilla-lineas revelar">
            <div>
                <?= $icono('<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>', 28) ?>
                <dt>Trazabilidad</dt><dd>Cada cambio queda en el historial: nada se modifica ni se borra sin dejar rastro.</dd>
            </div>
            <div>
                <?= $icono('<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>', 28) ?>
                <dt>Seguridad</dt><dd>Contraseñas encriptadas, sesiones, protección CSRF y aprobación de cada cuenta nueva.</dd>
            </div>
            <div>
                <?= $icono('<path d="M12 3v18M3 12h18"/><circle cx="12" cy="12" r="9"/>', 28) ?>
                <dt>Accesibilidad</dt><dd>Diseño adaptable a celulares, modo claro y oscuro, y navegación con teclado.</dd>
            </div>
        </dl>
    </div>
</section>

<section class="seccion seccion-final" aria-labelledby="titulo-final">
    <div class="contenedor">
        <div class="llamado revelar">
            <div class="llamado-anillos" aria-hidden="true"></div>
            <h2 id="titulo-final" class="degradado">¿Querés saber más del proyecto?</h2>
            <p>Escribinos con tus dudas o sugerencias, o pedí acceso para probar el sistema.</p>
            <div class="hero-acciones">
                <a class="boton boton-primario" href="contacto.php">Contactanos <?= $flecha ?></a>
                <?php if ($usuario): ?>
                    <a class="boton boton-secundario" href="app.php">Ir al sistema</a>
                <?php else: ?>
                    <a class="boton boton-secundario" href="registro.php">Crear cuenta</a>
                <?php endif; ?>
            </div>
        </div>
    </div>
</section>
<?php
pie();
