import argparse
import csv
import json
import logging
from collections import defaultdict

SEVERITY_MAP = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Утиліта для консолідації та аналізу логів антивірусного захисту"
    )
    parser.add_argument(
        "--edr-log", required=True, help="Шлях до вхідного JSON файлу логів"
    )
    parser.add_argument(
        "--min-severity",
        default="Low",
        choices=SEVERITY_MAP.keys(),
        help="Мінімальний рівень критичності",
    )
    parser.add_argument("--out-csv", required=True, help="Шлях до вихідного CSV файлу")
    parser.add_argument(
        "--log-file", required=True, help="Шлях до файлу системних логів"
    )
    return parser.parse_args()


def load_edr_logs(filepath: str) -> list:
    """Завантажує події з JSON-файлу."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        logging.error(f"Помилка читання файлу логів: {e}")  # noqa: LOG015
        return []


def process_events(events: list, min_severity: str):
    """Фільтрує події, агрегує статистику та шукає неліквідовані загрози."""
    min_severity_level = SEVERITY_MAP[min_severity]

    severity_counts = defaultdict(int)
    host_threat_counts = defaultdict(int)
    unresolved_threats = []

    for event in events:
        severity = event.get("Severity", "Low")

        if SEVERITY_MAP.get(severity, 0) < min_severity_level:
            continue

        severity_counts[severity] += 1

        host = event.get("Hostname", "Unknown")
        host_threat_counts[host] += 1

        action = event.get("ActionTaken", "Unknown")
        if action not in ("Quarantined", "Deleted"):
            unresolved_threats.append(event)
            logging.error(  # noqa: LOG015
                f"Unresolved threat detected: Host: {host}, Threat: {event.get('ThreatName')}, Action: {action}"
            )

    sorted_hosts = sorted(host_threat_counts.items(), key=lambda x: x[1], reverse=True)

    return severity_counts, sorted_hosts, unresolved_threats


def print_console_report(
    filepath: str,
    total_events: int,
    severity_counts: dict,
    sorted_hosts: list,
    unresolved_threats: list,
):
    """Виводить відформатований звіт у консоль."""
    print(f"[INFO] Aggregating EDR alerts from {filepath}...")
    print(f"[INFO] Processed {total_events} antivirus incident events.\n")

    print("=== Severity Distribution ===")
    for sev in ["Critical", "High", "Medium", "Low"]:
        if sev in severity_counts:
            print(f"{sev:<8} : {severity_counts[sev]}")
    print()

    print("=== Unresolved Security Threats (Action Not Quarantined/Deleted) ===")
    for t in unresolved_threats:
        sev_upper = t.get("Severity", "").upper()
        print(
            f"[{sev_upper}] Host: {t.get('Hostname')} | Threat: {t.get('ThreatName')} | Action: {t.get('ActionTaken')}"
        )
    print()

    print("=== Top Affected Hosts ===")
    for i, (host, count) in enumerate(sorted_hosts, 1):
        print(f"{i}. {host:<15} ({count} threats)")
    print()


def export_to_csv(filepath: str, sorted_hosts: list):
    """Зберігає агреговану статистику по хостах у CSV-файл."""
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Hostname", "Total_Incidents"])
            for host, count in sorted_hosts:
                writer.writerow([host, count])
        print(f"[INFO] Aggregated incident matrix saved to {filepath}")
    except Exception as e:  # noqa: BLE001
        logging.error(f"Помилка запису CSV файлу: {e}")  # noqa: LOG015


def main():
    args = parse_args()

    logging.basicConfig(
        filename=args.log_file,
        level=logging.ERROR,
        format="[%(asctime)s] %(levelname)s: %(message)s",
    )

    events = load_edr_logs(args.edr_log)
    if not events:
        return

    severity_counts, sorted_hosts, unresolved_threats = process_events(
        events, args.min_severity
    )

    print_console_report(
        args.edr_log, len(events), severity_counts, sorted_hosts, unresolved_threats
    )

    export_to_csv(args.out_csv, sorted_hosts)


if __name__ == "__main__":
    main()
