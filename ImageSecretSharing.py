import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np

PRIME = 257  # 使用質數 257 (適用於 8-bit 影像像素)

# ----------------------------------------------------------------------
# 數學與 Shamir 秘密分割演算法
# ----------------------------------------------------------------------
def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

def mod_inverse(a, m):
    gcd, x, _ = extended_gcd(a, m)
    if gcd != 1:
        raise Exception('不存在模逆元')
    return (x % m + m) % m

def split_image_array(img_array, k, n, p=PRIME):
    h, w, c = img_array.shape
    shares = [np.zeros((h, w, c), dtype=np.uint8) for _ in range(n)]
    
    coeffs = [np.random.randint(1, p, size=(h, w, c)) for _ in range(k - 1)]
    
    for i in range(1, n + 1):
        x = i
        y_val = img_array.astype(np.int64)
        term = x
        for coeff in coeffs:
            y_val = (y_val + coeff * term) % p
            term = (term * x) % p
            
        y_val = np.clip(y_val, 0, 255)
        shares[i - 1] = y_val.astype(np.uint8)
        
    return shares

def recover_image_array(selected_shares, share_indices, k, p=PRIME):
    h, w, c = selected_shares[0].shape
    recovered = np.zeros((h, w, c), dtype=np.float64)
    num_shares = len(selected_shares)
    
    for i in range(num_shares):
        xi = share_indices[i]
        yi = selected_shares[i].astype(np.float64)
        
        num = 1.0
        den = 1.0
        for j in range(num_shares):
            if i != j:
                xj = share_indices[j]
                num = (num * (-xj)) % p
                den = (den * (xi - xj)) % p
        
        lagrange_coeff = (num * mod_inverse(int(den) % p, p)) % p
        recovered = (recovered + yi * lagrange_coeff) % p
        
    recovered = np.clip(recovered, 0, 255)
    return recovered.astype(np.uint8)


# ----------------------------------------------------------------------
# GUI 介面設計
# ----------------------------------------------------------------------
class ImageSecretSharingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("機密影像 (k, n) 門檻式分割與還原系統")
        self.geometry("800x650")
        self.resizable(False, False)

        self.loaded_image = None
        self.img_array = None
        self.generated_shares = []
        self.share_arrays = []
        
        self.BG_COLOR = "#F4F6F9"
        self.CARD_BG = "#FFFFFF"
        self.PRIMARY_COLOR = "#2563EB"
        self.ACCENT_COLOR = "#10B981"
        self.TEXT_COLOR = "#1F2937"
        
        self.configure(bg=self.BG_COLOR)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TNotebook", background=self.BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Microsoft JhengHei", 11, "bold"), padding=[20, 10], background="#E5E7EB")
        self.style.map("TNotebook.Tab", background=[("selected", self.PRIMARY_COLOR)], foreground=[("selected", "#FFFFFF")])
        self.style.configure("Card.TFrame", background=self.CARD_BG, borderwidth=0)
        self.style.configure("Header.TLabel", font=("Microsoft JhengHei", 12, "bold"), background=self.CARD_BG, foreground=self.PRIMARY_COLOR)

        self.create_widgets()

    def create_widgets(self):
        header_frame = tk.Frame(self, bg=self.BG_COLOR)
        header_frame.pack(fill="x", padx=25, pady=(15, 5))
        
        tk.Label(header_frame, text="🖼️ 機密影像 (k, n)-Threshold 祕密分享系統", font=("Microsoft JhengHei", 16, "bold"), bg=self.BG_COLOR, fg=self.TEXT_COLOR).pack(anchor="w")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=15)

        self.tab_encode = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_decode = ttk.Frame(self.notebook, style="Card.TFrame")

        self.notebook.add(self.tab_encode, text=" 🔒 編碼端 (影像分割) ")
        self.notebook.add(self.tab_decode, text=" 🔓 解碼端 (影像還原) ")

        self.build_encode_tab()
        self.build_decode_tab()

    def build_encode_tab(self):
        frame = ttk.Frame(self.tab_encode, style="Card.TFrame", padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="1. 選擇機密影像 (Image Key)", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        btn_browse = tk.Button(frame, text="📁 瀏覽並載入圖片...", font=("Microsoft JhengHei", 9), command=self.on_load_image)
        btn_browse.grid(row=1, column=0, sticky="w", padx=5)
        self.lbl_img_path = tk.Label(frame, text="未選擇任何檔案", font=("Microsoft JhengHei", 9), bg=self.CARD_BG, fg="#6B7280")
        self.lbl_img_path.grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="2. 設定 (k, n)-threshold 參數", style="Header.TLabel").grid(row=2, column=0, columnspan=2, sticky="w", pady=(15, 5))
        
        param_frame = tk.Frame(frame, bg=self.CARD_BG)
        param_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

        tk.Label(param_frame, text="總碎片數 (n):", bg=self.CARD_BG).pack(side="left")
        self.spin_n = ttk.Spinbox(param_frame, from_=2, to=10, width=5)
        self.spin_n.pack(side="left", padx=(0, 20))
        self.spin_n.set(4)

        tk.Label(param_frame, text="解鎖門檻 (k):", bg=self.CARD_BG).pack(side="left")
        self.spin_k = ttk.Spinbox(param_frame, from_=2, to=10, width=5)
        self.spin_k.pack(side="left")
        self.spin_k.set(2)

        btn_split = tk.Button(frame, text="⚡ 切分影像並產生碎片", font=("Microsoft JhengHei", 10, "bold"), 
                              bg=self.PRIMARY_COLOR, fg="white", relief="flat", command=self.on_split_image)
        btn_split.grid(row=4, column=0, columnspan=2, sticky="w", pady=15)

        ttk.Label(frame, text="3. 原圖與碎片預覽", style="Header.TLabel").grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        
        self.preview_frame = tk.Frame(frame, bg="#F9FAFB", bd=1, relief="solid")
        self.preview_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=5)

    def on_load_image(self):
        file_path = filedialog.askopenfilename(
            title="選擇機密影像",
            filetypes=[
                ("所有支援圖片", "*.png *.jpg *.jpeg *.bmp"),
                ("PNG 圖片", "*.png"),
                ("JPEG 圖片", "*.jpg *.jpeg"),
                ("BMP 圖片", "*.bmp"),
                ("所有檔案", "*.*")
            ]
        )
        if file_path:
            self.lbl_img_path.config(text=file_path)
            img = Image.open(file_path).convert("RGB")
            # 將縮圖上限提高至 350x350，確保預覽與還原畫面更清晰且較大
            img.thumbnail((350, 350))
            self.loaded_image = img
            self.img_array = np.array(img)
            messagebox.showinfo("成功", "影像載入成功！")

    def on_split_image(self):
        if self.img_array is None:
            messagebox.showwarning("警告", "請先選擇並載入一張圖片！")
            return

        n = int(self.spin_n.get())
        k = int(self.spin_k.get())

        if k > n:
            messagebox.showwarning("錯誤", "k 必須小於或等於 n！")
            return

        self.share_arrays = split_image_array(self.img_array, k, n)
        self.generated_shares = [Image.fromarray(arr) for arr in self.share_arrays]

        for child in self.preview_frame.winfo_children():
            child.destroy()

        for idx, img in enumerate(self.generated_shares):
            img_tk = ImageTk.PhotoImage(img.resize((80, 80)))
            lbl = tk.Label(self.preview_frame, image=img_tk, text=f"碎片 #{idx+1}", compound="top", bg="#F9FAFB")
            lbl.image = img_tk
            lbl.pack(side="left", padx=10, pady=10)

        self.update_decode_checklist()
        messagebox.showinfo("完成", f"已成功將影像切分為 {n} 張碎片！")

    def build_decode_tab(self):
        frame = ttk.Frame(self.tab_decode, style="Card.TFrame", padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="1. 勾選任意 ≥ k 張碎片進行組合還原", style="Header.TLabel").pack(anchor="w", pady=5)
        
        self.check_frame = tk.Frame(frame, bg="#F9FAFB", bd=1, relief="solid")
        self.check_frame.pack(fill="x", pady=10)
        self.check_vars = []

        btn_recover = tk.Button(frame, text="🔓 還原原始影像", font=("Microsoft JhengHei", 10, "bold"), 
                                bg=self.ACCENT_COLOR, fg="white", relief="flat", command=self.on_recover_image)
        btn_recover.pack(anchor="w", pady=10)

        ttk.Label(frame, text="2. 還原結果預覽", style="Header.TLabel").pack(anchor="w", pady=5)
        self.lbl_recovered_img = tk.Label(frame, text="（尚未還原）", bg="#F3F4F6", height=8, width=30)
        self.lbl_recovered_img.pack(anchor="w", pady=5)

    def update_decode_checklist(self):
        for child in self.check_frame.winfo_children():
            child.destroy()
        self.check_vars.clear()

        for idx, arr in enumerate(self.share_arrays):
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(self.check_frame, text=f"影像碎片 #{idx+1}", variable=var, bg="#F9FAFB")
            chk.pack(side="left", padx=15, pady=15)
            self.check_vars.append((var, idx + 1, arr))

    def on_recover_image(self):
        selected = [(x_idx, arr) for var, x_idx, arr in self.check_vars if var.get()]
        k = int(self.spin_k.get())

        if len(selected) < k:
            messagebox.showwarning("碎片不足", f"需要至少 {k} 張碎片才能還原，目前僅選擇 {len(selected)} 張！")
            return

        x_indices = [item[0] for item in selected]
        shares = [item[1] for item in selected]

        recovered_arr = recover_image_array(shares, x_indices, k)
        recovered_img = Image.fromarray(recovered_arr)

        # 放大顯示還原結果 (例如放大至 250x250 預覽)
        w, h = recovered_img.size
        display_size = (250, int(250 * h / w)) if w > 0 else (250, 250)
        img_tk = ImageTk.PhotoImage(recovered_img.resize(display_size))
        
        self.lbl_recovered_img.config(image=img_tk, text="", width=display_size[0], height=display_size[1])
        self.lbl_recovered_img.image = img_tk


if __name__ == "__main__":
    app = ImageSecretSharingApp()
    app.mainloop()