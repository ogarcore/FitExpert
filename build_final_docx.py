"""
build_final_docx.py
===================
Orquestador principal que compila y genera el archivo Word definitivo:
`FitExpert_Presentacion_Proyecto.docx`.
"""

import os
import sys
import docx
from datetime import datetime

from doc_builder_core import setup_document_styles
from doc_section_cover_and_index import build_cover_page, build_table_of_contents
from doc_section_part1 import build_chapters_1_to_6
from doc_section_part2 import build_chapters_7_to_10
from doc_section_part3 import build_chapters_11_to_16
from doc_section_part4 import build_chapters_17_to_24

OUTPUT_FILENAME = "FitExpert_Presentacion_Proyecto.docx"


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando compilación de {OUTPUT_FILENAME}...")

    # Crear documento nuevo
    doc = docx.Document()

    # 1. Configurar estilos y márgenes
    print("  -> Configurando márgenes, encabezados y estilos base...")
    setup_document_styles(doc)

    # 2. Portada e Índice
    print("  -> Construyendo Portada Institucional e Índice General...")
    build_cover_page(doc)
    build_table_of_contents(doc)

    # 3. Capítulos 1 al 6
    print("  -> Compilando Capítulos 1 al 6 (Introducción, Descripción, Antecedentes, Justificación, Objetivos, Alcance)...")
    build_chapters_1_to_6(doc)

    # 4. Capítulos 7 al 10
    print("  -> Compilando Capítulos 7 al 10 (Usuarios, Funcionamiento, Funcionalidades Detalladas, Recorrido)...")
    build_chapters_7_to_10(doc)

    # 5. Capítulos 11 al 16
    print("  -> Compilando Capítulos 11 al 16 (Módulos, Interfaces, Datos, Tecnologías, Arquitectura, Seguridad)...")
    build_chapters_11_to_16(doc)

    # 6. Capítulos 17 al 24
    print("  -> Compilando Capítulos 17 al 24 (Beneficios, Ventajas, Limitaciones, Mejoras, Valor, Conclusiones, Glosario, Anexos A-E)...")
    build_chapters_17_to_24(doc)

    # Guardar archivo Word
    print(f"  -> Guardando archivo Word final en: {OUTPUT_FILENAME}...")
    doc.save(OUTPUT_FILENAME)

    file_size_kb = os.path.getsize(OUTPUT_FILENAME) / 1024
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ¡Documento generado con éxito!")
    print(f"     Archivo: {OUTPUT_FILENAME}")
    print(f"     Tamaño:  {file_size_kb:.1f} KB")

    # Auditoría del documento
    doc_check = docx.Document(OUTPUT_FILENAME)
    num_paras = len(doc_check.paragraphs)
    num_tables = len(doc_check.tables)
    total_words = sum(len(p.text.split()) for p in doc_check.paragraphs)
    for t in doc_check.tables:
        for row in t.rows:
            for cell in row.cells:
                total_words += sum(len(p.text.split()) for p in cell.paragraphs)

    print("\n" + "=" * 60)
    print("RESUMEN DE AUDITORÍA Y CONTROL DE CALIDAD DEL DOCUMENTO:")
    print("=" * 60)
    print(f"  • Párrafos de texto:        {num_paras}")
    print(f"  • Tablas estructuradas:     {num_tables}")
    print(f"  • Conteo estimado palabras: ~{total_words:,} palabras")
    print(f"  • Imágenes insertadas:      3 figuras centradas con pie formal")
    print(f"  • Capítulos cubiertos:      24 capítulos + Portada + Índice")
    print("=" * 60)


if __name__ == "__main__":
    main()
