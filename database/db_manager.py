import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from config import FIREBASE_CREDENTIALS_PATH
import os

class DBManager:
    def __init__(self):
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            
        self.db = firestore.client()
        self.transactions = self.db.collection('transactions')
        self.categories = self.db.collection('categories')
        
        self._init_default_categories()
        
    def _init_default_categories(self):
        """Khởi tạo danh mục mặc định nếu chưa có."""
        docs = self.categories.limit(1).get()
        if len(docs) == 0:
            default_inflow = ["Lương", "Thưởng", "Thu nhập thụ động", "Bán hàng", "Khác"]
            default_outflow = ["Ăn uống", "Hóa đơn", "Di chuyển", "Mua sắm", "Sức khỏe", "Giải trí", "Khác"]
            
            for cat in default_inflow:
                self.categories.add({"name": cat, "type": "inflow"})
            for cat in default_outflow:
                self.categories.add({"name": cat, "type": "outflow"})
                
    def get_categories(self, t_type="outflow"):
        """Lấy danh sách tên danh mục theo loại."""
        query = self.categories.where(filter=firestore.FieldFilter("type", "==", t_type))
        return [doc.to_dict().get("name") for doc in query.stream()]

    def add_transaction(self, t_type, total_amount, items, date, general_note, image_path, contact_person):
        """Thêm giao dịch mới vào CSDL."""
        doc = {
            "type": t_type,
            "total_amount": float(total_amount),
            "items": items,
            "date": date,
            "general_note": general_note,
            "image_path": image_path,
            "contact_person": contact_person,
            "created_at": datetime.now()
        }
        update_time, doc_ref = self.transactions.add(doc)
        return doc_ref.id

    def get_transactions(self, start_date=None, end_date=None, sort_by="date", direction=-1):
        """Lấy danh sách giao dịch, mặc định sắp xếp mới nhất lên đầu."""
        query = self.transactions
        if start_date and end_date:
            query = query.where(filter=firestore.FieldFilter("date", ">=", start_date)).where(filter=firestore.FieldFilter("date", "<=", end_date))
            
        if direction == -1:
            query = query.order_by(sort_by, direction=firestore.Query.DESCENDING)
        else:
            query = query.order_by(sort_by, direction=firestore.Query.ASCENDING)
            
        results = []
        for doc in query.stream():
            data = doc.to_dict()
            data['_id'] = doc.id
            results.append(data)
        return results
        
    def delete_transaction(self, transaction_id):
        """Xóa giao dịch"""
        return self.transactions.document(transaction_id).delete()

    def get_transaction_by_id(self, transaction_id):
        """Lấy thông tin một giao dịch theo ID"""
        doc = self.transactions.document(transaction_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['_id'] = doc.id
            return data
        return None

    def update_transaction(self, transaction_id, t_type, total_amount, items, date, general_note, image_path, contact_person):
        """Cập nhật giao dịch đã tồn tại"""
        doc = {
            "type": t_type,
            "total_amount": float(total_amount),
            "items": items,
            "date": date,
            "general_note": general_note,
            "image_path": image_path,
            "contact_person": contact_person,
            "updated_at": datetime.now()
        }
        return self.transactions.document(transaction_id).update(doc)

    def get_summary_by_date_range(self, start_date, end_date):
        """Tính tổng thu / chi trong một khoảng thời gian."""
        transactions = self.get_transactions(start_date, end_date)
        
        summary = {"inflow": 0.0, "outflow": 0.0}
        for t in transactions:
            t_type = t.get("type")
            if t_type in summary:
                summary[t_type] += t.get("total_amount", 0.0)
                
        summary["balance"] = summary["inflow"] - summary["outflow"]
        return summary

    def get_summary_by_category(self, start_date, end_date, t_type="outflow"):
        """Tính tổng số tiền thu/chi theo từng hạng mục trong một khoảng thời gian."""
        transactions = self.get_transactions(start_date, end_date)
        
        cat_summary = {}
        for t in transactions:
            if t.get("type") == t_type:
                for item in t.get("items", []):
                    cat_name = item.get("category_name")
                    amount = item.get("amount", 0.0)
                    if cat_name not in cat_summary:
                        cat_summary[cat_name] = 0.0
                    cat_summary[cat_name] += amount
                    
        result = [{"_id": k, "total": v} for k, v in cat_summary.items()]
        result.sort(key=lambda x: x["total"], reverse=True)
        return result
