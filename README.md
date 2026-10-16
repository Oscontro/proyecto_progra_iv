# Sistema de Inventario de Equipos de Radio

Aplicación web para gestionar un parque de equipos de radiocomunicación: inventario,
ingreso de equipos con su programación de canales, circuito de reparación en taller,
stock de repuestos por taller, papelera, estadísticas y administración de usuarios.

Proyecto Integrador (2º parcial) · Programación IV · HTML5, CSS, JavaScript, PHP y MySQL/MariaDB.

---

## Contenido

- [Funcionalidades](#funcionalidades)
- [Cómo cumple la consigna](#cómo-cumple-la-consigna)
- [Tecnologías](#tecnologías)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación local (XAMPP)](#instalación-local-xampp)
- [Publicación en un hosting](#publicación-en-un-hosting)
- [Base de datos](#base-de-datos)
- [Seguridad](#seguridad)
- [Herramientas para desarrollo](#herramientas-para-desarrollo)
- [Decisiones de diseño](#decisiones-de-diseño)

---

## Funcionalidades

**Sitio público**

| Página | Qué hace |
|---|---|
| Portada (`web/index.php`) | Nombre del sistema, menú, descripción y accesos a registro e ingreso |
| Contacto (`web/contacto.php`) | Mapa de Google (UTN Facultad Regional Haedo) y formulario de consulta |
| Registro (`web/registro.php`) | Alta de usuarios generales; la cuenta queda pendiente hasta que un administrador la aprueba |
| Ingreso (`web/ingresar.php`) | Login con usuario y contraseña |
| Error (`web/error.php`) | Destino del login fallido y de los accesos sin sesión |

**Aplicación** (`web/app.php`, requiere sesión)

| Pestaña | Técnico | Administrador |
|---|:---:|:---:|
| Ingreso de equipos: alta con programación de canales, importación desde Excel | ✅ | ✅ |
| Inventario: buscador, filtros, historial, exportación a Excel, edición, envío a papelera y a taller | ✅ | ✅ |
| Taller: recepción, estados y egreso registrando los repuestos usados | ✅ | ✅ |
| Repuestos: catálogo y stock por taller | ✅ | ✅ (las bajas, solo admin) |
| Papelera: restaurar equipos | ✅ | ✅ (la baja definitiva, solo admin) |
| Estadísticas | ✅ | ✅ |
| Administración: usuarios, aprobación de registros, reseteo de claves | — | ✅ |
| Consultas: mensajes recibidos por el formulario de contacto | — | ✅ |

## Cómo cumple la consigna

| Requisito | Dónde |
|---|---|
| Base MySQL con al menos 3 tablas (contactos, usuarios, contenido principal) | `contactos`, `usuarios`, `equipos` y 25 tablas más (`db/schema.sql`) |
| Dos niveles de usuario y contraseñas encriptadas | Administrador / Técnico (`usuarios.es_administrador`); `password_hash()` / `password_verify()` |
| Página principal con nombre, menú, descripción, registro y login | `web/index.php`, `web/registro.php`, `web/ingresar.php` |
| Contacto con mapa de Google y formulario PHP con `mail()` que guarda en la base | `web/contacto.php` → tabla `contactos` y `mail()` a una dirección simulada (`php/config.php`) |
| Login verificado con sesión de PHP; si falla, redirige a una página de error | `$_SESSION` en `php/sesion.php`; `web/ingresar.php` → `web/error.php?codigo=…` |
| Usuario general: página interna con contenido de la base | `web/app.php` (Inventario, Taller, Estadísticas…) |
| Administrador: página adicional con ABM | Altas, bajas y modificaciones de equipos, repuestos, usuarios y consultas |
| Al menos un buscador | Buscadores y filtros en Inventario, Taller, Repuestos, Papelera, Administración y Consultas |

## Tecnologías

- **Frontend:** HTML5, CSS y JavaScript (módulos ES, sin frameworks). Excel en el navegador con [SheetJS](https://sheetjs.com/) (`web/vendor/sheetjs`, licencia Apache 2.0).
- **Backend:** PHP 8.1 o superior (probado con 8.2) con PDO. Las páginas públicas son PHP que genera HTML; la aplicación consulta una API JSON (`php/*.php`).
- **Base de datos:** MariaDB 10.4 (probado; un MySQL compatible también debería funcionar). Solo tablas
  InnoDB con claves foráneas: no usa vistas, triggers ni procedimientos almacenados, que los hostings
  gratuitos no permiten. Esa lógica (historial de cambios, stock total de repuestos, circuito de taller)
  está en PHP (`php/historial_comun.php` y los endpoints).

## Estructura del proyecto

```
proyecto_progra_iv/
├── README.md
└── InventarioAR-main/          ← carpeta que se publica
    ├── index.php               redirige a web/
    ├── web/                    sitio y aplicación
    │   ├── index.php, contacto.php, registro.php, ingresar.php, error.php, salir.php
    │   ├── app.php             aplicación (zona protegida)
    │   ├── inc/                encabezado, pie y base común de las páginas (bloqueada por HTTP)
    │   ├── js/                 app.js, api.js, ui.js… y pestanas/*.js (una por pestaña)
    │   ├── css/                app.css (aplicación) y sitio.css (páginas públicas)
    │   ├── img/                logo
    │   └── vendor/sheetjs/     librería de Excel
    ├── php/                    API JSON
    │   ├── config.php          configuración (se sobrescribe con config.local.php)
    │   ├── conexion.php        cabeceras y respuestas JSON de la API
    │   ├── sesion.php          sesión de PHP, login, CSRF
    │   ├── auth.php            requireAuth() / requireAdmin() para los endpoints
    │   ├── *_comun.php         lógica compartida (equipos, repuestos, usuarios)
    │   └── *.php               un archivo por endpoint
    ├── resources/images/       imágenes de los modelos de equipos
    ├── db/
    │   ├── schema.sql          estructura completa de la base (sin datos)
    │   └── migraciones/        cambios de estructura, en orden de fecha
    ├── tools/
    │   ├── snapshot_api.php    red de seguridad: captura y compara respuestas de la API
    │   └── armar_publicacion.sh  arma el paquete y el volcado de la base para el hosting
    └── retirado/               código fuera de uso (bloqueado por HTTP)
```

La carpeta también conserva el cliente de escritorio original en Python (`main.py`, `tabs/`…),
del que se migró la aplicación. Ya no se usa y no hace falta publicarlo.

## Instalación local (XAMPP)

1. Clonar el repositorio dentro de `C:\xampp\htdocs\` y arrancar Apache y MySQL.

2. Crear la base e importar la estructura:

   ```bash
   mysql -u root -e "CREATE DATABASE inventario_radios CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
   mysql -u root --default-character-set=utf8mb4 inventario_radios < InventarioAR-main/db/schema.sql
   ```

   `schema.sql` ya incluye todas las migraciones. (Si se parte de un volcado viejo, aplicar
   las de `db/migraciones/` en orden de fecha.)

3. *(Opcional)* Copiar `php/config.local.example.php` como `php/config.local.php` y cambiar
   solo lo necesario (credenciales de la base, `api_debug`, dirección de contacto).
   Sin ese archivo se usan los valores de `php/config.php`: `root` sin contraseña sobre `inventario_radios`.

4. Crear el primer administrador. Generar el hash de una contraseña inicial:

   ```bash
   php -r "echo password_hash('CambiarEstaClave1', PASSWORD_DEFAULT), PHP_EOL;"
   ```

   e insertarlo (por consola o desde phpMyAdmin):

   ```sql
   INSERT INTO usuarios (legajo, username, nombre, apellido, email, password_hash,
                         es_administrador, debe_cambiar_clave, activo)
   VALUES ('0001', 'admin', 'Administrador', 'Sistema', NULL, '<hash generado>', 1, 1, 1);
   ```

   Con `debe_cambiar_clave = 1` el sistema obliga a cambiar esa contraseña en el primer ingreso.
   Los demás usuarios se crean desde **Administración** o se registran desde la portada.

5. Abrir <http://localhost/proyecto_progra_iv/InventarioAR-main/>.

## Publicación en InfinityFree

El plan gratuito de [InfinityFree](https://www.infinityfree.com/) tiene PHP 8 y MariaDB 10.4, con
InnoDB y claves foráneas, pero **no** permite vistas, triggers, procedimientos, funciones ni eventos
(el usuario de la base solo tiene ALTER, CREATE, DELETE, DROP, INDEX, INSERT, SELECT, UPDATE y
LOCK TABLES). Por eso la base del proyecto es solo de tablas. Tampoco hay `mail()`.

1. **Crear la cuenta y la base.** En el panel: *MySQL Databases* → crear una base (queda
   `if0_NNNNNNNN_nombre`). Anotar host (`sqlNNN.infinityfree.com`), usuario y contraseña
   (la de la cuenta de hosting, en *Account Details*).
2. **Configuración.** Copiar `php/config.local.example.php` como `php/config.hosting.php` (no se
   versiona) y completar `db_host`, `db_user`, `db_pass` y `db_name`.
3. **Armar el paquete** (Git Bash, desde la raíz del repositorio):

   ```bash
   bash InventarioAR-main/tools/armar_publicacion.sh
   ```

   Genera en `publicacion/` (no se versiona):
   - `htdocs/` y `htdocs.zip`: solo `index.php`, `.htaccess`, `web/`, `php/` y `resources/`, con
     `config.hosting.php` incluido como `php/config.local.php`. Nada del cliente de escritorio,
     `db/`, `tools/` ni logs.
   - `base_para_hosting.sql`: tablas y datos de la base local, sin `CREATE DATABASE`. **Tiene datos
     reales y hashes de contraseñas: no compartirlo ni versionarlo.**
4. **Importar la base.** En el panel → *phpMyAdmin* de la base creada → *Importar* →
   `base_para_hosting.sql`.
5. **Subir los archivos** dentro de `htdocs/` del sitio: por FTP (FileZilla, con los datos de
   *FTP Details*) o con el *File Manager* del panel, subiendo `htdocs.zip` y extrayéndolo ahí.
   Borrar el `index2.html` que crea InfinityFree.
6. **HTTPS.** Panel → *Free SSL Certificates* → emitir el certificado del dominio. Con HTTPS la
   cookie de sesión se marca `Secure` automáticamente.
7. **Probar:** portada, registro, ingreso, contacto, y como administrador aprobar el registro,
   un alta de equipo y un envío a taller.

Notas:
- **`mail()`** no funciona en InfinityFree. La consulta de contacto se guarda igual en la tabla
  `contactos` (`mail_enviado = 0`), la página lo informa y el administrador la ve en la pestaña
  **Consultas**.
- **`sql_mode` y zona horaria:** cada conexión fija el `sql_mode` con el que se desarrolló y la
  hora de Argentina (`php/config.php`), así el comportamiento no depende de la configuración del servidor.
- **`Options -Indexes`** en `.htaccess`: si algún hosting no lo permite (error 500), borrar esa línea.
- InfinityFree muestra una verificación del navegador en la primera visita; por eso herramientas
  como `tools/snapshot_api.php` (sin navegador) no funcionan contra el sitio publicado.

## Base de datos

Tablas principales:

| Tabla | Contenido |
|---|---|
| `usuarios` | Cuentas, perfil (`es_administrador`), estado, aprobación pendiente, bloqueo por intentos |
| `equipos` | Inventario de equipos (tipo, marca, modelo, serie, escala, sector, estado) |
| `tipos`, `marcas`, `modelos`, `escalas` | Catálogos |
| `programacion_canales`, `canales_detalle` | Programación de frecuencias de cada equipo |
| `taller_recepcion`, `taller_ingresos`, `taller_egresos`, `taller_egreso_repuestos`, `equipo_estado` | Circuito de taller |
| `repuestos`, `repuesto_stock`, `modelo_repuesto` | Repuestos, stock por taller y compatibilidad con modelos |
| `papelera`, `historial_equipos`, `observaciones_*` | Bajas, auditoría y observaciones |
| `contactos` | Consultas del formulario de contacto |

**Migraciones** (`db/migraciones/`): cada cambio de estructura es un archivo `.sql` fechado. Para aplicarlo:

```bash
mysql -u root --default-character-set=utf8mb4 inventario_radios < db/migraciones/AAAA-MM-DD_descripcion.sql
```

Después de aplicar una migración se regenera `schema.sql`:

```bash
mysqldump -u root --no-data --skip-triggers --skip-comments --default-character-set=utf8mb4 inventario_radios \
  | sed -E 's/ AUTO_INCREMENT=[0-9]+//' > db/schema.sql
```

Los volcados con datos **no se versionan** (`.gitignore` excluye `*.sql` salvo el esquema y las migraciones).

## Seguridad

- **Sesión de PHP** (`$_SESSION`, cookie `HttpOnly` y `SameSite=Lax`): el usuario se vuelve a validar contra
  la base en cada pedido. Desactivar una cuenta o resetear su contraseña invalida sus sesiones abiertas.
  La sesión vence a las 2 horas sin actividad o a las 12 horas del ingreso.
- **Contraseñas** con `password_hash()`. Tras 5 intentos fallidos la cuenta se bloquea 15 minutos.
- **Claves temporales** aleatorias al crear un usuario o resetear su clave: se muestran una sola vez al
  administrador y obligan a cambiarla en el primer ingreso.
- **CSRF:** los formularios llevan un token de sesión; la API exige el header `X-Requested-With`.
- **Formularios públicos** con campo trampa contra robots y límite de envíos por sesión.
- **Consultas SQL** con sentencias preparadas (PDO). Los datos se insertan en la página como texto, nunca como HTML.
- **`.htaccess`** bloquea volcados, logs, código del escritorio, `db/`, `tools/`, `retirado/` y `web/inc/`,
  y desactiva los listados de carpetas. `Content-Security-Policy` en todas las páginas.
- Un administrador no puede desactivarse, eliminarse ni quitarse el perfil a sí mismo, y siempre queda
  al menos un administrador activo.

## Herramientas para desarrollo

`tools/snapshot_api.php` captura las respuestas de los endpoints de lectura y las compara entre dos
momentos, para detectar cambios no buscados en la API:

```bash
cd InventarioAR-main
API_USER=admin API_PASS=... php tools/snapshot_api.php capturar tools/snapshots/antes
# ... cambios ...
API_USER=admin API_PASS=... php tools/snapshot_api.php capturar tools/snapshots/despues
php tools/snapshot_api.php comparar tools/snapshots/antes tools/snapshots/despues
```

Ingresa por el formulario como lo haría el navegador. Las capturas contienen datos reales: quedan fuera de git.

## Decisiones de diseño

- **Migración desde un cliente de escritorio** (Python + PyQt6) a la web, por fases. Las etiquetas
  `pre-migracion` y `pre-fase-4` marcan el estado original y el fin de la migración de pantallas.
- **Pestañas retiradas:** Vehículos, Etiquetas, Configuración y Últimos movimientos (código en `retirado/`).
- **Catálogos con confirmación:** si al ingresar un equipo se escribe un tipo, marca, modelo o escala
  que no existe, se pide confirmación antes de crearlo (nada se crea sin avisar).
- **Egreso de taller con repuestos reales:** el egreso descuenta del stock del taller los repuestos del
  catálogo compatibles con el modelo y los registra en `taller_egreso_repuestos`.
- **Registro con aprobación:** las cuentas creadas desde la portada quedan pendientes hasta que un
  administrador las aprueba.
- **Excel en el navegador:** las exportaciones e importaciones se hacen con SheetJS, sin librerías de PHP.
