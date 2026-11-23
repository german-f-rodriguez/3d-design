# Soporte para display de 7"

Soporte impreso en 3D para montar un display de 100 × 165 × 5 mm sobre la cara bottom de una PCB de 124 × 165,05 mm. La base es pasante: las láminas EMC de la PCB tocan el dorso metálico del display.

## Piezas

| Archivo | Cantidad | Medidas (mm) |
|---|---|---|
| `base.stl` | 1 | 124 × 170 × 6,5, con reborde de apoyo de 3 × 1,5 |
| `marco.stl` | 1 | 124 × 170 × 3 |
| `separador_x4.stl` | 4 | Ø10 × 3, agujero Ø4 |

`DisplaySupport.FCStd` contiene el conjunto armado, con la PCB, el display, el flex y el componente alto como referencias (`Ref_*`).

## Armado

De la PCB hacia el frente: PCB, separadores, base, display y marco. El dorso del display queda a 4,5 mm de la PCB, así que las láminas de 5 mm se comprimen 0,5 mm. El flex sale por la ranura de la base y pasa por la muesca de la PCB.

Los tornillos atraviesan 14,1 mm de apilado. Con un tornillo de 20 mm, contando la cabeza, quedan 5,9 mm de rosca en la estructura. El tipo de rosca está pendiente de confirmar: parece M3 × 0,5, pero la foto no descarta #4-40 UNC.

## Impresión

Todas las piezas se imprimen planas y sin soportes. La base va con el reborde sobre la cama y el marco con los avellanados hacia arriba. El reborde es delgado, así que conviene manipular la base con cuidado.

## Cómo modificarlo

Cambia las medidas al inicio de `display_support.py` y ejecuta:

```
freecadcmd display_support.py
```

El script vuelve a generar el `.FCStd` y los `.stl`, y falla si encuentra un sólido inválido o una interferencia.

## Medidas a comprobar antes de imprimir

| Medida | Valor usado | Origen |
|---|---|---|
| Altura de las láminas | ≈5 mm | Aproximada |
| Compresión de las láminas | 0,5 mm | Supuesto |
| Posición de las láminas | Dentro de la ventana de la base | Supuesto |
| Componente alto | X desde 110 mm, Y de 57 a 97 mm, 6 mm de alto | Aproximado; la Y se estimó de una foto |
| Altura máxima bajo el display | 4,5 mm | Limitación del diseño |
| Altura máxima bajo la base | 3 mm | Limitación del diseño |
| Diámetro de los agujeros de la PCB | ≈5,5 mm (3) y ≈4,2 mm (1); solo afectan a la referencia | Medido sobre la imagen |
| Margen de los agujeros a los bordes laterales | 5,5 mm | (124 − 113) / 2 |
| Profundidad de la muesca | 2 mm | Medida sobre la imagen |
| Ancho del flex | ≈30 mm, de Y ≈ 67,5 a 97,5 mm | Estimado de una foto |
| Espacio libre arriba y abajo de la PCB | 2,5 mm | La base y el marco sobresalen de la PCB |
| Espesor de la PCB | 1,6 mm | Supuesto |
