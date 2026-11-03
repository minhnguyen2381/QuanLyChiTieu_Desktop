"""Thêm key danh mục cho dữ liệu cũ trên Firestore.

    python -m scripts.migrate_category_keys            # dry-run: chỉ đọc và báo cáo
    python -m scripts.migrate_category_keys --apply    # backup ra backups/ rồi ghi

Chỉ THÊM field (`key` cho categories, `category_key` cho từng item), không xoá field cũ,
nên dữ liệu đã migrate vẫn đọc được bằng bản app cũ. Nhưng một khi bản mới đã tạo/sửa giao dịch
(chỉ ghi category_key) thì KHÔNG quay về bản cũ được nữa. Chạy lại nhiều lần an toàn. Hãy đóng app trước khi chạy.
"""
import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime

from app.config import BACKUPS_DIR, FIREBASE_CREDENTIALS_PATH
from app.domain.categories import is_legacy_name, legacy_name_to_key
from app.infrastructure.firestore_mapping import transaction_from_document

MISSING_NAME = "<missing>"
BATCH_LIMIT = 400  # Firestore cho tối đa 500 thao tác mỗi batch


@dataclass
class MigrationPlan:
    category_updates: dict[str, dict] = field(default_factory=dict)
    transaction_updates: dict[str, dict] = field(default_factory=dict)
    unknown_names: set[str] = field(default_factory=set)

    @property
    def is_empty(self) -> bool:
        return not self.category_updates and not self.transaction_updates


def plan_migration(category_docs: dict[str, dict], transaction_docs: dict[str, dict]) -> MigrationPlan:
    """Hàm thuần: tính các field cần thêm, không đụng tới Firestore."""
    plan = MigrationPlan()

    def key_for(name: str | None) -> str:
        if not name:
            plan.unknown_names.add(MISSING_NAME)
        elif not is_legacy_name(name):
            plan.unknown_names.add(name)
        return legacy_name_to_key(name)

    for doc_id, data in category_docs.items():
        if not data.get("key"):
            plan.category_updates[doc_id] = {"key": key_for(data.get("name"))}

    for doc_id, data in transaction_docs.items():
        items = data.get("items", [])
        if all(item.get("category_key") for item in items):
            continue
        plan.transaction_updates[doc_id] = {"items": [
            item if item.get("category_key") else {**item, "category_key": key_for(item.get("category_name"))}
            for item in items
        ]}
    return plan


def find_unreadable_transactions(transaction_docs: dict[str, dict]) -> dict[str, str]:
    """Doc mà app mới không đọc được (validate domain lỗi) -> thông báo lỗi. Một doc lỗi làm hỏng cả kỳ."""
    errors = {}
    for doc_id, data in transaction_docs.items():
        try:
            transaction_from_document(doc_id, data)
        except Exception as error:
            errors[doc_id] = f"{type(error).__name__}: {error}"
    return errors


def find_fractional_amounts(transaction_docs: dict[str, dict]) -> list[str]:
    """Doc có số tiền lẻ (không nguyên): UI làm tròn VND khi sửa nên sẽ đổi giá trị."""
    return sorted(
        doc_id for doc_id, data in transaction_docs.items()
        if any(isinstance(amount := item.get("amount"), (int, float)) and not isinstance(amount, bool)
               and not float(amount).is_integer() for item in data.get("items", []))
    )


def write_backup(category_docs: dict, transaction_docs: dict, backups_dir: str) -> str:
    os.makedirs(backups_dir, exist_ok=True)
    path = os.path.join(backups_dir, f"firestore_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump({"categories": category_docs, "transactions": transaction_docs}, file,
                  ensure_ascii=False, indent=2, default=_json_default)
    return path


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Không backup được kiểu {type(value).__name__}")


def _read_collection(client, name: str) -> tuple[dict[str, dict], dict[str, object]]:
    """Trả về (dữ liệu theo id, update_time theo id)."""
    docs, update_times = {}, {}
    for snapshot in client.collection(name).stream():
        docs[snapshot.id] = snapshot.to_dict()
        update_times[snapshot.id] = snapshot.update_time
    return docs, update_times


def _apply(client, collection: str, updates: dict[str, dict], update_times: dict[str, object]) -> int:
    """Ghi theo batch; mỗi doc kèm điều kiện 'chưa bị sửa từ lúc đọc' để không ghi đè thay đổi mới."""
    doc_ids = list(updates)
    for start in range(0, len(doc_ids), BATCH_LIMIT):
        batch = client.batch()
        for doc_id in doc_ids[start:start + BATCH_LIMIT]:
            option = client.write_option(last_update_time=update_times[doc_id])
            batch.update(client.collection(collection).document(doc_id), updates[doc_id], option=option)
        batch.commit()
    return len(doc_ids)


def _print_report(plan: MigrationPlan, category_count: int, transaction_count: int) -> None:
    print(f"categories:   {len(plan.category_updates)}/{category_count} doc cần thêm 'key'")
    print(f"transactions: {len(plan.transaction_updates)}/{transaction_count} doc cần thêm 'category_key'")
    if plan.unknown_names:
        print("Tên danh mục không có trong bảng ánh xạ (sẽ dùng nguyên tên làm key):")
        for name in sorted(plan.unknown_names):
            print(f"  - {name}")


def _print_readability(transaction_docs: dict[str, dict], applying: bool) -> None:
    unreadable = find_unreadable_transactions(transaction_docs)
    print(f"transactions: {len(unreadable)} doc app mới KHÔNG đọc được (cả kỳ chứa doc đó sẽ lỗi khi tải)")
    for doc_id, message in sorted(unreadable.items()):
        print(f"  - {doc_id}: {message}")
    fractional = find_fractional_amounts(transaction_docs)
    if fractional:
        print(f"transactions: {len(fractional)} doc có số tiền lẻ (UI sẽ làm tròn khi sửa): {', '.join(fractional)}")
    else:
        print("transactions: không có doc nào có số tiền lẻ")
    if unreadable and applying:
        print("CẢNH BÁO: vẫn migrate (chỉ thêm field), nhưng các doc trên cần sửa tay để app mới đọc được.")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="backup rồi ghi lên Firestore (mặc định: dry-run)")
    args = parser.parse_args(argv)

    from app.infrastructure.firestore_repository import connect  # import chậm: test không cần Firebase
    client = connect(FIREBASE_CREDENTIALS_PATH)
    category_docs, category_times = _read_collection(client, "categories")
    transaction_docs, transaction_times = _read_collection(client, "transactions")
    plan = plan_migration(category_docs, transaction_docs)
    _print_report(plan, len(category_docs), len(transaction_docs))
    _print_readability(transaction_docs, args.apply)

    if not args.apply:
        print("\nDry-run: chưa ghi gì. Chạy lại với --apply để ghi.")
        return 0
    if plan.is_empty:
        print("\nKhông có gì cần migrate.")
        return 0

    try:
        backup_path = write_backup(category_docs, transaction_docs, BACKUPS_DIR)
    except (OSError, TypeError) as error:
        print(f"\nBackup thất bại, dừng lại, chưa ghi gì: {error}", file=sys.stderr)
        return 1
    print(f"\nĐã backup: {backup_path}")

    written = _apply(client, "categories", plan.category_updates, category_times)
    written += _apply(client, "transactions", plan.transaction_updates, transaction_times)
    print(f"Đã ghi {written} doc. Chạy lại (không --apply) để kiểm tra: kết quả phải là 0 doc cần sửa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
