<?php
// Sitemap XML de las páginas públicas, con la URL del sitio en que se publique.
// No usa la base ni la sesión: solo la plantilla, por urlBase().
require_once __DIR__ . '/inc/plantilla.php';

header('Content-Type: application/xml; charset=utf-8');
$base = urlBase();
$paginas = ['' => '1.0', 'contacto.php' => '0.6', 'registro.php' => '0.5', 'ingresar.php' => '0.4'];

echo '<?xml version="1.0" encoding="UTF-8"?>', "\n";
echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', "\n";
foreach ($paginas as $pagina => $prioridad) {
    $archivo = __DIR__ . '/' . ($pagina ?: 'index.php');
    printf("  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n",
        htmlspecialchars($base . $pagina, ENT_XML1, 'UTF-8'), date('Y-m-d', filemtime($archivo)), $prioridad);
}
echo '</urlset>', "\n";
