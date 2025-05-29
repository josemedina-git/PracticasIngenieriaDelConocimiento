import time
import json
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def cerrar_modal_si_esta_abierto(driver, intentos=3):
    """Función para cerrar modales que puedan interferir con el scraping"""
    for intento in range(intentos):
        try:
            modales = driver.find_elements(By.CSS_SELECTOR, ".modal")
            modal_visible = None
            for m in modales:
                if m.is_displayed():
                    modal_visible = m
                    break
            
            if not modal_visible:
                return
            
            print(f"Modal detectado, cerrando... (intento {intento+1})")
            
            try:
                close_icon = modal_visible.find_element(By.CSS_SELECTOR, "i.icon-close.close")
                driver.execute_script("arguments[0].click();", close_icon)
                WebDriverWait(driver, 5).until(lambda d: not modal_visible.is_displayed())
                print("✅ Modal cerrado")
                return
            except:
                # Forzar cierre con JavaScript
                driver.execute_script("""
                    document.querySelectorAll('.modal').forEach(modal => {
                        modal.style.display = 'none';
                        modal.classList.remove('in');
                    });
                    document.body.classList.remove('modal-open');
                    document.querySelectorAll('.modal-backdrop').forEach(backdrop => 
                        backdrop.remove()
                    );
                """)
                time.sleep(1)
                return

        except Exception as e:
            print(f"⚠️ Error cerrando modal: {e}")
            continue

def obtener_disponibilidad_aguascalientes(driver):
    """Obtiene la disponibilidad específicamente para Aguascalientes"""
    try:
        print("🗺 Buscando disponibilidad en tiendas...")
        
        # Buscar el botón de geolocalización/tiendas
        geo_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btnGeoStore"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", geo_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", geo_button)

        # Esperar a que aparezcan los estados
        print("⏳ Cargando estados...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.a-product__anchorSelectState"))
        )
        
        # Buscar Aguascalientes
        estados_links = driver.find_elements(By.CSS_SELECTOR, "a.a-product__anchorSelectState")
        aguascalientes_link = None
        
        for link in estados_links:
            if "aguascalientes" in link.text.lower():
                aguascalientes_link = link
                break
        
        if not aguascalientes_link:
            print("❌ Aguascalientes no encontrado")
            return []

        print("✅ Aguascalientes encontrado, seleccionando...")
        driver.execute_script("arguments[0].scrollIntoView();", aguascalientes_link)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", aguascalientes_link)

        # Esperar tiendas
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li > div.a-product__store"))
        )

        tiendas = driver.find_elements(By.CSS_SELECTOR, "li > div.a-product__store")
        datos_tiendas = []
        
        for tienda in tiendas:
            try:
                parrafos = tienda.find_elements(By.TAG_NAME, "p")
                if len(parrafos) >= 2:
                    nombre_tienda = parrafos[0].text.strip()
                    existencia = parrafos[1].text.strip()
                    
                    # Solo Villa Asunción y Altaria (múltiples variaciones del nombre)
                    keywords_tiendas = [
                        "altaria", 
                        "villa asuncion", 
                        "villaasuncion", 
                        "villasuncion",  # Como aparece en la imagen
                        "villa suncion",
                        "aguascalientes villasuncion",
                        "aguascalientes villa"
                    ]
                    if any(keyword in nombre_tienda.lower() for keyword in keywords_tiendas):
                        datos_tiendas.append({
                            "tienda": nombre_tienda,
                            "existencia": existencia
                        })
                        print(f"  📍 {nombre_tienda}: {existencia}")
                        
            except StaleElementReferenceException:
                continue

        cerrar_modal_si_esta_abierto(driver)
        return datos_tiendas

    except Exception as e:
        print(f"❌ Error obteniendo disponibilidad: {e}")
        cerrar_modal_si_esta_abierto(driver)
        return []

def obtener_info_producto(driver):
    """Obtiene información del producto actual"""
    try:
        # Nombre del producto
        nombre_elemento = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.a-product__information--title"))
        )
        nombre = nombre_elemento.text.strip()
        
        # Precio
        try:
            precio_elemento = driver.find_element(By.CSS_SELECTOR, ".a-product__paragraphPriceProduct")
            precio = precio_elemento.text.strip()
        except:
            precio = "Precio no disponible"
            
        return nombre, precio
    except Exception as e:
        print(f"⚠️ Error obteniendo info del producto: {e}")
        return "Producto desconocido", "Precio no disponible"

def buscar_celulares_gama_alta():
    """Función principal de scraping"""
    # Configurar Chrome
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    resultados = []

    try:
        print("🚀 Iniciando Liverpool...")
        driver.get("https://www.liverpool.com.mx/")
        time.sleep(3)  # Esperar que cargue completamente

        print("🔍 Realizando búsqueda...")
        
        # Buscar el campo de búsqueda
        search_box = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "mainSearchbar"))
        )
        
        # Limpiar y escribir
        search_box.clear()
        search_box.send_keys("celulares de gama alta")
        time.sleep(2)
        
        # Buscar
        search_box.send_keys(Keys.RETURN)
        
        print("⏳ Esperando resultados...")
        time.sleep(5)  # Esperar que carguen los resultados
        
        # Verificar que estamos en página de resultados
        current_url = driver.current_url
        print(f"📍 URL actual: {current_url}")
        
        if "search" not in current_url.lower() and "buscar" not in current_url.lower():
            print("⚠️ Puede que no estemos en página de resultados, continuando...")
        
        # Buscar productos
        productos_links = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/tienda/pdp/']"))
        )
        
        print(f"📱 {len(productos_links)} productos encontrados")
        
        # Tomar los primeros 5
        urls_productos = []
        for i in range(min(5, len(productos_links))):
            url = productos_links[i].get_attribute("href")
            if url:
                urls_productos.append(url)
                print(f"  {i+1}. {url}")

        # Procesar cada producto
        for i, url in enumerate(urls_productos, 1):
            print(f"\n{'='*60}")
            print(f"📱 PRODUCTO {i}/5")
            print(f"{'='*60}")
            
            try:
                driver.get(url)
                time.sleep(3)
                
                nombre_producto, precio_producto = obtener_info_producto(driver)
                print(f"📱 {nombre_producto}")
                print(f"💰 {precio_producto}")
                
                disponibilidad = obtener_disponibilidad_aguascalientes(driver)
                
                resultado = {
                    "producto_numero": i,
                    "nombre": nombre_producto,
                    "precio": precio_producto,
                    "url": url,
                    "disponibilidad_aguascalientes": disponibilidad
                }
                
                resultados.append(resultado)
                
                if disponibilidad:
                    print(f"✅ {len(disponibilidad)} tiendas con disponibilidad")
                else:
                    print("❌ Sin disponibilidad en Aguascalientes")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error en producto {i}: {e}")
                continue

        return resultados

    except Exception as e:
        print(f"❌ Error general: {e}")
        # Captura de pantalla para debug
        try:
            driver.save_screenshot("error_screenshot.png")
            print("📸 Captura guardada como error_screenshot.png")
        except:
            pass
        return []

    finally:
        driver.quit()

def guardar_resultados(resultados):
    """Guarda resultados en JSON y CSV"""
    if not resultados:
        print("❌ No hay resultados para guardar")
        return
    
    # JSON
    with open("celulares_aguascalientes.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("✅ JSON guardado: celulares_aguascalientes.json")
    
    # CSV
    with open("celulares_aguascalientes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Producto", "Nombre", "Precio", "URL", "Tienda", "Disponibilidad"])
        
        for resultado in resultados:
            if resultado["disponibilidad_aguascalientes"]:
                for tienda in resultado["disponibilidad_aguascalientes"]:
                    writer.writerow([
                        resultado["producto_numero"],
                        resultado["nombre"],
                        resultado["precio"],
                        resultado["url"],
                        tienda["tienda"],
                        tienda["existencia"]
                    ])
            else:
                writer.writerow([
                    resultado["producto_numero"],
                    resultado["nombre"],
                    resultado["precio"],
                    resultado["url"],
                    "Sin tiendas",
                    "No disponible"
                ])
    
    print("✅ CSV guardado: celulares_aguascalientes.csv")

if __name__ == "__main__":
    print("🏪 SCRAPER LIVERPOOL - CELULARES AGUASCALIENTES")
    print("=" * 60)
    
    resultados = buscar_celulares_gama_alta()
    
    if resultados:
        print(f"\n🎉 Completado: {len(resultados)} productos analizados")
        guardar_resultados(resultados)
        
        print("\n📊 RESUMEN:")
        print("-" * 40)
        for resultado in resultados:
            print(f"📱 {resultado['nombre'][:40]}...")
            if resultado["disponibilidad_aguascalientes"]:
                for tienda in resultado["disponibilidad_aguascalientes"]:
                    print(f"   📍 {tienda['tienda']}: {tienda['existencia']}")
            else:
                print("   ❌ Sin disponibilidad")
            print()
    else:
        print("❌ No se obtuvieron resultados")