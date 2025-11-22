import pyautogui
import pygetwindow as gw
import time
from datetime import datetime, timedelta
import sys

# ========================= НАСТРОЙКИ =========================
WINDOW_TITLE = "Clinical app"  # Название окна
TOTAL_DURATION_MINUTES = 120  # Сколько минут работать (например 120 = 2 часа)
# или можно задать количество циклов:
# TOTAL_CYCLES = 60                    # вместо TOTAL_DURATION_MINUTES

PAUSE_BETWEEN_ACTIONS = 0.5  # пауза между действиями pyautogui (безопасность, НЕ ТРОГАТЬ!)
pyautogui.PAUSE = PAUSE_BETWEEN_ACTIONS

# Координаты (нужно откалибровать под экран один раз!)
INPUT_FIELD_X = 218  # координата поля ввода названия файла
INPUT_FIELD_Y = 118

CREATE_DIR_BUTTON_X = 420  # кнопка "Create directory"
CREATE_DIR_BUTTON_Y = 120

SFDI_BUTTON_X = 697  # координата кнопки SFDI
SFDI_BUTTON_Y = 171

SFDI_DIRECTORY = 'name=TEST_type=OGTT-7_time='  # Имя папки измерений
# =============================================================

def activate_clinical_window():
    windows = gw.getWindowsWithTitle(WINDOW_TITLE)
    if not windows:
        print(f"[!] Окно '{WINDOW_TITLE}' не найдено!")
        return False
    window = windows[0]
    if window.isMinimized:
        window.restore()
    window.activate()
    time.sleep(1)
    return True


def get_current_time_suffix():
    return datetime.now().strftime("%H-%M")


def create_directory_cycle():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Начинаю цикл...")

    if not activate_clinical_window():
        return False

    # Клик в поле ввода имени директории
    pyautogui.click(INPUT_FIELD_X, INPUT_FIELD_Y)
    time.sleep(0.5)

    # Очищаем поле
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.press('backspace')
    time.sleep(0.3)

    # Формируем имя
    time_suffix = get_current_time_suffix()
    directory_name = f"{SFDI_DIRECTORY}{time_suffix}"
    print(f"Ввожу имя: {directory_name}")
    pyautogui.write(directory_name, interval=0.05)

    # Нажимаем кнопку SFDI
    print("Нажимаю кнопку SFDI...")
    pyautogui.click(SFDI_BUTTON_X, SFDI_BUTTON_Y)
    time.sleep(2)  # даём приложению время на обработку

    print("Цикл завершён\n")
    return True


# ==================== КАЛИБРОВКА КООРДИНАТ ====================
def calibrate_coordinates():
    print("КАЛИБРОВКА: Наведи курсор на нужные элементы и нажимай Enter:")
    print("1. Поле ввода имени директори")
    input("Наведи курсор - нажми Enter")
    x, y = pyautogui.position()
    print(f"Поле ввода: {x, y}")

    print("2. Кнопка SFDI (вкладка вверху)")
    input("Наведи курсор - нажми Enter")
    x2, y2 = pyautogui.position()
    print(f"Кнопка SFDI: {x2, y2}")

    print("\nСкопируй эти координаты в скрипт выше:")
    print(f"INPUT_FIELD_X, INPUT_FIELD_Y = {x}, {y}")
    print(f"SFDI_BUTTON_X, SFDI_BUTTON_Y = {x2}, {y2}")
    sys.exit()


# =============================================================

if __name__ == "__main__":
    print("=== Автоматизация Clinical app ===\n")

    # Если хочешь откалибровать координаты - раскомментируй строку ниже и запусти один раз
    # calibrate_coordinates()

    print("Запуск через 10 секунд... Переключись на окно Clinical app!")
    time.sleep(10)

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=TOTAL_DURATION_MINUTES)
    cycle_count = 0

    try:
        while True:
            current_time = datetime.now()
            if current_time >= end_time:
                print(f"Достигнуто время окончания: {TOTAL_DURATION_MINUTES} минут")
                break

            cycle_count += 1
            success = create_directory_cycle()
            if not success:
                print("Окно не найдено — остановка")
                break

            print(f"Ожидание 2 минуты до следующего цикла... (цикл {cycle_count})")
            time.sleep(120)  # 2 минуты
    except KeyboardInterrupt:
        print("\nОстановлено пользователем")

    print(f"\nГотово! Выполнено циклов: {cycle_count}")
