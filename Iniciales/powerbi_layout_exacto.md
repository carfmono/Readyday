# Estructura exacta del reporte Power BI

## Tamaño recomendado
- Página: 16:9
- Fondo: blanco
- Margen visual externo: 16 px
- Separación entre visuales: 10–12 px

## Página 1: Resumen diario
### Franja superior (altura aprox. 120 px)
1. **Slicer de fecha**  
   - Ubicación: esquina superior izquierda  
   - Tamaño: 240 x 60  
   - Tipo: Between o Relative date

2. **Card: Recovery Score**  
   - Ubicación: fila superior, centro-izquierda  
   - Tamaño: 180 x 90

3. **Card: Strain Score**  
   - Ubicación: a la derecha de Recovery  
   - Tamaño: 180 x 90

4. **Card: Balance Score**  
   - Ubicación: a la derecha de Strain  
   - Tamaño: 180 x 90

5. **Card: Readiness Zone**  
   - Ubicación: extremo derecho superior  
   - Tamaño: 180 x 90  
   - Fondo condicional:
     - Verde -> #DCFCE7
     - Amarillo -> #FEF3C7
     - Rojo -> #FEE2E2

### Bloque central izquierdo
6. **Línea: Recovery vs Strain (30 días)**  
   - Ubicación: columna izquierda, debajo de cards  
   - Tamaño: 620 x 290  
   - Eje X: Date  
   - Valores: Recovery_Score, Strain_Score

### Bloque central derecho
7. **Tarjeta multilínea: Recommendation_Text**  
   - Ubicación: arriba a la derecha del bloque central  
   - Tamaño: 320 x 130

8. **Gauge o KPI: Body Battery Morning**  
   - Ubicación: debajo de Recommendation  
   - Tamaño: 155 x 145

9. **Gauge o KPI: Sleep Score**  
   - Ubicación: al lado de Body Battery  
   - Tamaño: 155 x 145

### Franja inferior
10. **Columnas: Training Minutes por día**  
    - Ubicación: abajo izquierda  
    - Tamaño: 300 x 200

11. **Línea: HRV vs Baseline 28d**  
    - Ubicación: abajo centro  
    - Tamaño: 300 x 200

12. **Tabla compacta: hábitos del día**  
    - Ubicación: abajo derecha  
    - Tamaño: 320 x 200  
    - Campos:
      - Date
      - LateCoffee
      - LateDinner
      - IllnessFlag
      - StressAvg

---

## Página 2: Sueño y recuperación
1. **Card: Sleep Score promedio 7d** — arriba izquierda
2. **Card: HRV promedio 7d** — arriba centro
3. **Card: Fatigue Label** — arriba derecha
4. **Área/Línea: Sleep Score 30 días** — centro izquierda grande
5. **Línea: HRV y HRV Baseline 28d** — centro derecha grande
6. **Matriz: días con rojo/amarillo/verde** — franja inferior completa

---

## Página 3: Carga y entrenamiento
1. **Card: Training Load** — arriba izquierda
2. **Card: Stress Load** — arriba centro
3. **Card: Strain Trend 7d** — arriba derecha
4. **Columnas apiladas: carga por tipo de día** — centro izquierda
5. **Scatter: StressAvg vs Recovery_Score** — centro derecha
6. **Tabla detalle** con Date, TrainingMin, Intensity, Strain_Score, Balance_Score — parte inferior

---

## Interacciones recomendadas
- El slicer de fecha debe filtrar todas las visuales
- Desactivar interacción entre tabla detalle y cards KPI
- Mantener interacción entre línea de 30 días y scatter

## Orden visual recomendado
- Recovery -> Strain -> Balance -> Recomendación
- Luego tendencias
- Luego detalle de hábitos y entrenamiento

## Jerarquía de color
- Primario: azul
- Secundario: verde azulado
- Advertencia: ámbar
- Riesgo: rojo suave
- Neutro: gris claro

## Tipografía sugerida
- Segoe UI o Aptos
- Cards: 28–34 pt
- Títulos de visual: 11–12 pt
- Tablas: 10–11 pt

## Campos que conviene ocultar en el panel
- Intensity original si creas una dimensión
- Flags auxiliares de color
- Columnas de apoyo para baseline o normalización si decides moverlas a Power Query