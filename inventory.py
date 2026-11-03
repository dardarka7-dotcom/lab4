import json
import platform
import socket
from datetime import datetime

import psutil


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M"),
    }


def get_cpu_info():
    freq = psutil.cpu_freq()
    return {
        "model": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_freq_mhz": round(freq.max) if freq else None,
        "load_percent": psutil.cpu_percent(interval=1),
    }


def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / 1024**3, 1),
        "used_percent": mem.percent,
        "available_gb": round(mem.available / 1024**3, 1),
    }


def get_disk_info():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fs": part.fstype,
            "total_gb": round(usage.total / 1024**3, 1),
            "used_percent": usage.percent,
        })
    return disks


def get_network_info():
    """Сбор сетевых интерфейсов (имя, IPv4, маска, MAC)."""
    net_interfaces = []
    addrs = psutil.net_if_addrs()
    for name, interface in addrs.items():
        ipv4_addr = None
        netmask = None
        mac_addr = None
        for addr in interface:
            if addr.family == socket.AF_INET:
                ipv4_addr = addr.address
                netmask = addr.netmask
            elif addr.family == psutil.AF_LINK:
                mac_addr = addr.address
        if ipv4_addr:
            net_interfaces.append({
                "interface": name,
                "ipv4": ipv4_addr,
                "netmask": netmask,
                "mac": mac_addr
            })
    return net_interfaces


def analyze(passport):
    """Автоматический анализ паспорта и генерация рекомендаций."""
    recs = []
    ram_total = passport["memory"]["total_gb"]
    cpu_phys = passport["cpu"]["physical_cores"]

    if ram_total < 8:
        recs.append("Недостаточно памяти для виртуальных машин и Docker")
    if ram_total >= 16 and cpu_phys >= 6:
        recs.append("Подходит для одновременной работы нескольких VM")

    for disk in passport["disks"]:
        if disk["used_percent"] > 85:
            recs.append(f"Освободить место на диске {disk['mountpoint']}")

    if cpu_phys < 4:
        recs.append("Процессор может стать узким местом (bottleneck)")

    if passport["cpu"]["load_percent"] > 50:
        recs.append("Высокая начальная загрузка процессора")

    return recs


def main():
    passport = {
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": get_system_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disks": get_disk_info(),
        "network": get_network_info(),
    }
    passport["recommendations"] = analyze(passport)

    filename = f"passport_{passport['system']['hostname']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(passport, f, indent=2, ensure_ascii=False)
    print(json.dumps(passport, indent=2, ensure_ascii=False))
    print(f"\nПаспорт сохранён в файл {filename}")


if __name__ == "__main__":
    main()