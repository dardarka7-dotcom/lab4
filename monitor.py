import csv
import time
from datetime import datetime

import psutil

INTERVAL = 1          # секунд между замерами (Вариант 1)
SAMPLES = 30          # количество замеров (Вариант 1)
THRESHOLDS = {"cpu": 70, "ram": 80, "disk": 85}  # Пороги под Вариант 1
LOG_FILE = "monitor_log.csv"


def take_sample():
    return {
        "time": datetime.now().strftime("%H:%M:%S"),
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "processes": len(psutil.pids())  # Дополнительная метрика для Варианта 1
    }


def check_alerts(sample):
    alerts = []
    for metric, limit in THRESHOLDS.items():
        if sample[metric] >= limit:
            alerts.append(f"{metric.upper()} = {sample[metric]}% (порог {limit}%)")
    return alerts


def main():
    psutil.cpu_percent(interval=None)  # «прогреваем» замер CPU
    samples_data = []

    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "cpu", "ram", "disk", "processes", "alert"])
        writer.writeheader()

        for _ in range(SAMPLES):
            time.sleep(INTERVAL)
            s = take_sample()
            alerts = check_alerts(s)
            s["alert"] = "; ".join(alerts)
            writer.writerow(s)
            samples_data.append(s)

            mark = "  <-- ВНИМАНИЕ: " + s["alert"] if alerts else ""
            print(f"{s['time']} | CPU: {s['cpu']:5.1f}% | RAM: {s['ram']:5.1f}% | DISK: {s['disk']:5.1f}% | Proc: {s['processes']}{mark}")

    print(f"\nЖурнал сохранён в {LOG_FILE}")

    # Статистика
    print("\n--- ИТОГОВАЯ СТАТИСТИКА МОНИТОРИНГА ---")
    for metric in ["cpu", "ram", "disk", "processes"]:
        values = [item[metric] for item in samples_data]
        avg_val = sum(values) / len(values)
        max_val = max(values)
        min_val = min(values)
        if metric == "processes":
            print(f"{metric.upper():<10}: Мин = {min_val}, Макс = {max_val}, Среднее = {avg_val:.1f}")
        else:
            print(f"{metric.upper():<10}: Мин = {min_val:.1f}%, Макс = {max_val:.1f}%, Среднее = {avg_val:.1f}%")


if __name__ == "__main__":
    main()