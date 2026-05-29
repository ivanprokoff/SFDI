# SFDI Fitter

Библиотека для обработки данных SFDI (Spatial Frequency Domain Imaging).

## Основные компоненты

### SFDIStack

`SFDIStack` — основная структура данных для хранения SFDI-изображений.

```python
from sfdi_fitter.data import SFDIStack, StackAxis
import numpy as np

stack = SFDIStack(
    data=np.ndarray,                      # данные стэка
    axis_names=[StackAxis.FREQUENCY,      # имена осей
                StackAxis.PHASE, 
                StackAxis.X, 
                StackAxis.Y],
    spatial_frequencies=[0.0, 0.1, 0.2],  # опционально: пространственные частоты
    parameter_names=['mac', 'mdc'],       # опционально: имена параметров
    wavelengths=[650, 730, 850]           # опционально: длины волн
)
```

#### Ключевые методы SFDIStack

**Работа с осями:**
- `get_axis_index(axis: StackAxis)` — получить индекс оси
- `reorder_axes(new_order: List[StackAxis])` — переупорядочить оси
- `get_noncoord_axes()` — получить не-координатные оси (FREQUENCY, PHASE, WAVELENGTH, RESULTS)
- `squeeze(axis_name: StackAxis)` — удалить оси размером 1

**Итерация по осям:**
```python
# Итерация по частотам и длинам волн
for (freq_idx, wl_idx), slice_data in stack.iterate_over_axes(
    StackAxis.FREQUENCY, StackAxis.WAVELENGTH
):
    process(slice_data)
```

### SFDIPipeline

`SFDIPipeline` — конвейер для последовательной обработки стэков через цепочку процессоров.

```python
from sfdi_fitter.pipeline import SFDIPipeline
from sfdi_fitter.demodulation import ClassicalDemodulator, CosConvolveDemodulator

pipeline = SFDIPipeline(processors=[
    ("demodulate", CosConvolveDemodulator(convolution_period=10)),
    ("normalize", NormalizeProcessor()),
    ("fit", FitterProcessor()),
])
```

#### Обработка через pipeline

```python
# Базовая обработка
processed_stack = pipeline.process(input_stack)

# С параметрами для отдельных шагов
processed_stack = pipeline.process(
    input_stack,
    demodulate__convolution_period=15,  # параметр для шага "demodulate"
    fit__max_iterations=100             # параметр для шага "fit"
)
```

Формат передачи параметров: `имя_шага__имя_аргумента`.

#### Доступ к процессорам

```python
# Получить процессор по индексу
name, processor = pipeline[0]

# Получить срез пайплайна
sub_pipeline = pipeline[1:3]
```

### Процессоры

Все процессоры наследуются от абстрактного класса `Processor` и реализуют метод `process(sfdi_stack: SFDIStack) -> SFDIStack`.

**Доступные процессоры демодуляции:**

- `ClassicalDemodulator` — классическая демодуляция по нескольким фазам
- `CosConvolveDemodulator` — демодуляция через свёртку с косинусом (single-shot)

```python
# Классическая демодуляция
demod = ClassicalDemodulator(
    add_dc=True,           # добавить DC-компоненту
    phase_ids=[0, 1, 2],   # индексы фаз
    mdc_freq_id=0          # индекс частоты для MDC
)

# Single-shot демодуляция
demod = CosConvolveDemodulator(
    convolution_period=10,  # период свёртки
    add_dc=True,
    mdc_freq_id=0
)

result = demod.process(stack)
```

## Пример полного пайплайна

```python
from sfdi_fitter import SFDIPipeline, SFDIStack
from sfdi_fitter.demodulation import CosConvolveDemodulator
from sfdi_fitter.data import StackAxis

# Создание стэка
stack = SFDIStack(
    data=raw_data,
    axis_names=[StackAxis.FREQUENCY, StackAxis.PHASE, StackAxis.X, StackAxis.Y],
    spatial_frequencies=[0.0, 0.05, 0.1]
)

# Построение пайплайна
pipeline = SFDIPipeline([
    ("demodulate", CosConvolveDemodulator(convolution_period=12)),
])

# Обработка
demodulated = pipeline.process(stack)
```

---

# TODO:

+ Добавить направление свёртки в ConvCosDemodulator?
+ продумать логику вычисления отражения (сейчас реализовано со старым кодом -- мб развязать)
+ реализовать алгоритмы SingleShotDemodulator

- реализовать логику с несколькими длинами волн в ReflectanceCalculator / Fitter
- переписать readme.md

Подумать(?)
- изменить логику calculate reflectance stack -- там много лишнего
- упаковать всё в пакет (установка eigen-exp-fitter?)
- реализовать трекинг операций над стэком?