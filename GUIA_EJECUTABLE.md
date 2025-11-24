# 🛠️ Cómo crear el ejecutable de BiblioHispa

¿Quieres convertir la biblioteca en un archivo `.exe` que funcione sin instalar nada más? ¡Sigue estos pasos! 🚀

## 1️⃣ Instala PyInstaller
Es la herramienta mágica que empaqueta todo. Abre la terminal y escribe:

```bash
pip install pyinstaller
```

## 2️⃣ Crea el ejecutable
Hemos preparado un archivo de configuración para que sea súper fácil. Solo tienes que ejecutar:

```bash
pyinstaller bibliohispa.spec
```

Esto leerá la configuración y empezará a empaquetar la aplicación, las plantillas HTML y las imágenes. Tardará un poquito... ⏳

## 3️⃣ ¡Listo!
Cuando termine, verás una carpeta nueva llamada `dist`. Dentro encontrarás tu archivo:

👉 **`dist/bibliohispa.exe`** (o solo `bibliohispa` si estás en Linux/Mac)

Puedes mover ese archivo donde quieras. Al ejecutarlo:
1.  Se abrirá una ventana negra (la consola del servidor).
2.  Creará automáticamente la base de datos `bibliohispa.db` y la carpeta `uploads` **en el mismo lugar donde esté el ejecutable**.
3.  Solo tienes que ir a tu navegador y escribir `http://localhost:5000`.

---

### 📝 Notas importantes

*   **Antivirus:** A veces los antivirus se ponen nerviosos con los `.exe` creados caseramente. Si te da problemas, añade una excepción.
*   **Base de datos:** Si mueves el `.exe` a otro ordenador, recuerda que la base de datos se creará nueva (vacía) a menos que te lleves también el archivo `bibliohispa.db` que se crea a su lado.
*   **Modo Ventana:** Si no quieres ver la consola negra, puedes editar el archivo `bibliohispa.spec` y cambiar `console=True` a `console=False`, y volver a ejecutar el comando del paso 2. Pero recomendamos dejarla al principio para ver si hay errores.

¡Que lo disfrutes! 🏗️🎉
