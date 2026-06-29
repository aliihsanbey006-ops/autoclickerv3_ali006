import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import pyautogui
import keyboard
import time
import os

class AutoclickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hibrit Autoclicker Kontrol Paneli")
        self.root.geometry("650x700")
        self.root.resizable(False, False)
        
        self.is_running = False
        
        # Görev listesi artık hem görsel hem koordinat tutabilir:
        # [{"tur": "Görsel", "hedef": "yol", "sure": 3.0, "adet": 5, "hiz": 0.1, "son_tiklama": 0}]
        # [{"tur": "Koordinat", "hedef": "X,Y", "sure": 2.0, "adet": 10, "hiz": 0.01, "son_tiklama": 0}]
        self.gorev_listesi = []
        
        self.create_widgets()
        
        # F4 Kısayolu
        keyboard.add_hotkey('F4', self.stop_clicking)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # --- BAŞLIK ---
        tk.Label(self.root, text="🤖 Hibrit Makro & Bot Sistemi", font=("Arial", 14, "bold")).pack(pady=5)
        tk.Label(self.root, text="Acil Durdurma Kısayolu: F4", fg="red", font=("Arial", 10, "bold")).pack(pady=2)
        
        # --- SEKME / SEÇİM ALANI (TÜRLER) ---
        frame_ekle = tk.LabelFrame(self.root, text=" Görev Tanımlama Alanı ")
        frame_ekle.pack(fill="x", padx=15, pady=5, ipady=5)
        
        # Görev Türü Seçimi (Radyo Butonları)
        self.gorev_turu = tk.StringVar(value="Görsel")
        
        tk.Radiobutton(frame_ekle, text="Görsel Odaklı", variable=self.gorev_turu, value="Görsel", font=("Arial", 10, "bold"), command=self.arayuz_guncelle).grid(row=0, column=0, padx=20, pady=5)
        tk.Radiobutton(frame_ekle, text="Koordinat Odaklı", variable=self.gorev_turu, value="Koordinat", font=("Arial", 10, "bold"), command=self.arayuz_guncelle).grid(row=0, column=1, padx=20, pady=5)
        
        # GÖRSEL SEÇİM BİLEŞENLERİ
        self.secilen_resim_yolu = ""
        self.btn_resim_sec = tk.Button(frame_ekle, text="Görsel Seç (.png)", command=self.resim_sec, bg="#e1e1e1")
        self.btn_resim_sec.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="we")
        self.lbl_secilen_ad = tk.Label(frame_ekle, text="Görsel seçilmedi...", fg="gray")
        self.lbl_secilen_ad.grid(row=2, column=0, columnspan=2, padx=15)
        
        # KOORDİNAT SEÇİM BİLEŞENLERİ (İlk başta gizli/pasif veya görünür yapabiliriz, aşağıda yöneteceğiz)
        self.lbl_x = tk.Label(frame_ekle, text="X:")
        self.entry_x = tk.Entry(frame_ekle, width=6)
        self.lbl_y = tk.Label(frame_ekle, text="Y:")
        self.entry_y = tk.Entry(frame_ekle, width=6)
        self.btn_koor_yakala = tk.Button(frame_ekle, text="Koordinat Yakala (3sn)", command=self.koordinat_yakala, bg="#cfd8dc")
        
        # ORTAK PARAMETRELER (Süre, Adet, Hız)
        frame_param = tk.Frame(frame_ekle)
        frame_param.grid(row=4, column=0, columnspan=2, pady=10, sticky="we")
        
        tk.Label(frame_param, text="Periyot (sn):").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.entry_periyot = tk.Entry(frame_param, width=6)
        self.entry_periyot.insert(0, "3.0")
        self.entry_periyot.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        tk.Label(frame_param, text="Tıklama Adedi:").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        self.entry_tiklama_sayisi = tk.Entry(frame_param, width=6)
        self.entry_tiklama_sayisi.insert(0, "1")
        self.entry_tiklama_sayisi.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        
        tk.Label(frame_param, text="Gecikme (sn):").grid(row=0, column=4, padx=5, pady=2, sticky="e")
        self.entry_tiklama_hizi = tk.Entry(frame_param, width=6)
        self.entry_tiklama_hizi.insert(0, "0.1")
        self.entry_tiklama_hizi.grid(row=0, column=5, padx=5, pady=2, sticky="w")
        
        # EKLE BUTONU
        tk.Button(frame_ekle, text="Görevi Listeye Ekle", bg="#FF9800", fg="white", font=("Arial", 10, "bold"), command=self.gorev_ekle).grid(row=5, column=0, columnspan=2, padx=15, pady=5, sticky="we")

        # --- BÖLÜM 2: GÖREV LİSTESİ (TABLO) ---
        frame_liste = tk.LabelFrame(self.root, text=" Görev Akış Sıralaması (Task List) ")
        frame_liste.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Tablo tasarımı (Tür sütunu eklendi)
        self.tablo = ttk.Treeview(frame_liste, columns=("Tur", "Hedef", "Periyot", "Adet", "Hiz"), show="headings", height=8)
        self.tablo.heading("Tur", text="Tür")
        self.tablo.heading("Hedef", text="Hedef (Görsel/Koor)")
        self.tablo.heading("Periyot", text="Periyot")
        self.tablo.heading("Adet", text="Adet")
        self.tablo.heading("Hiz", text="Hız (sn)")
        
        self.tablo.column("Tur", width=80, anchor="center")
        self.tablo.column("Hedef", width=180, anchor="w")
        self.tablo.column("Periyot", width=70, anchor="center")
        self.tablo.column("Adet", width=60, anchor="center")
        self.tablo.column("Hiz", width=70, anchor="center")
        self.tablo.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Silme Butonu
        tk.Button(frame_liste, text="Seçilen\nGörevi\nSil", bg="#757575", fg="white", font=("Arial", 9, "bold"), command=self.gorev_sil).pack(side="right", padx=5, fill="y", pady=5)

        # --- KONTROL BUTONLARI ---
        self.btn_baslat = tk.Button(self.root, text="SİSTEMİ BAŞLAT", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), command=self.start_bot)
        self.btn_baslat.pack(fill="x", padx=15, pady=5)
        
        self.btn_durdur = tk.Button(self.root, text="DURDUR (F4)", bg="#000000", fg="white", font=("Arial", 12, "bold"), command=self.stop_clicking, state="disabled")
        self.btn_durdur.pack(fill="x", padx=15, pady=5)
        
        # İlk arayüz durumunu ayarla
        self.arayuz_guncelle()

    # --- DİNAMİK ARAYÜZ YÖNETİMİ ---
    def arayuz_guncelle(self):
        """Seçilen moda göre butonları gizler veya gösterir."""
        if self.gorev_turu.get() == "Görsel":
            # Koordinat elemanlarını gizle
            self.lbl_x.grid_remove()
            self.entry_x.grid_remove()
            self.lbl_y.grid_remove()
            self.entry_y.grid_remove()
            self.btn_koor_yakala.grid_remove()
            # Görsel elemanlarını göster
            self.btn_resim_sec.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="we")
            self.lbl_secilen_ad.grid(row=2, column=0, columnspan=2, padx=15)
        else:
            # Görsel elemanlarını gizle
            self.btn_resim_sec.grid_remove()
            self.lbl_secilen_ad.grid_remove()
            # Koordinat elemanlarını göster
            self.lbl_x.grid(row=1, column=0, sticky="e", padx=5)
            self.entry_x.grid(row=1, column=1, sticky="w", padx=5)
            self.lbl_y.grid(row=2, column=0, sticky="e", padx=5)
            self.entry_y.grid(row=2, column=1, sticky="w", padx=5)
            self.btn_koor_yakala.grid(row=3, column=0, columnspan=2, padx=15, pady=5, sticky="we")

    # --- VERİ TOPLAMA İŞLEMLERİ ---
    def resim_sec(self):
        dosya = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if dosya:
            self.secilen_resim_yolu = dosya
            self.lbl_secilen_ad.config(text=os.path.basename(dosya), fg="green")

    def koordinat_yakala(self):
        def geri_sayim():
            for i in range(3, 0, -1):
                self.root.title(f"Mousu Hedefe Götür! ({i})")
                time.sleep(1)
            x, y = pyautogui.position()
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, str(x))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, str(y))
            self.root.title("Hibrit Autoclicker Kontrol Paneli")
        threading.Thread(target=geri_sayim).start()

    def gorev_ekle(self):
        tur = self.gorev_turu.get()
        try:
            sure = float(self.entry_periyot.get())
            adet = int(self.entry_tiklama_sayisi.get())
            hiz = float(self.entry_tiklama_hizi.get())
            if sure <= 0 or adet <= 0 or hiz < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Lütfen sayısal değerleri doğru ve pozitif girin!")
            return
        
        if tur == "Görsel":
            if not self.secilen_resim_yolu:
                messagebox.showwarning("Uyarı", "Lütfen bir görsel seçin!")
                return
            hedef_deger = self.secilen_resim_yolu
            gosterilecek_ad = os.path.basename(self.secilen_resim_yolu)
        else:
            try:
                x = int(self.entry_x.get())
                y = int(self.entry_y.get())
                hedef_deger = f"{x},{y}"
                gosterilecek_ad = f"Koordinat: ({x}, {y})"
            except ValueError:
                messagebox.showwarning("Uyarı", "Lütfen X ve Y koordinatlarını geçerli girin!")
                return

        # Listeye kaydet
        self.gorev_listesi.append({
            "tur": tur,
            "hedef": hedef_deger,
            "sure": sure,
            "adet": adet,
            "hiz": hiz,
            "son_tiklama": 0.0
        })
        
        # Tabloya ekle
        self.tablo.insert("", "end", values=(tur, gosterilecek_ad, f"{sure}s", f"{adet}x", f"{hiz}s"))
        
        # Temizlik
        self.secilen_resim_yolu = ""
        self.lbl_secilen_ad.config(text="Görsel seçilmedi...", fg="gray")

    def gorev_sil(self):
        secili_item = self.tablo.selection()
        if not secili_item: return
        for item in secili_item:
            index = self.tablo.index(item)
            self.gorev_listesi.pop(index)
            self.tablo.delete(item)

    # --- BOT KONTROL VE ANA MOTOR ---
    def start_bot(self):
        if not self.gorev_listesi:
            messagebox.showwarning("Uyarı", "Listede hiç görev yok!")
            return
        self.is_running = True
        self.btn_baslat.config(state="disabled")
        self.btn_durdur.config(state="normal")
        
        t = threading.Thread(target=self.hibrit_bot_motoru)
        t.daemon = True
        t.start()

    def stop_clicking(self):
        if self.is_running:
            self.is_running = False
            print("--- BOT DURDURULDU (F4) ---")
            self.btn_baslat.config(state="normal")
            self.btn_durdur.config(state="disabled")

    def hibrit_bot_motoru(self):
        print("Hibrit bot çalışmaya başladı...")
        simdi = time.time()
        for g in self.gorev_listesi:
            g["son_tiklama"] = simdi - g["sure"]

        while self.is_running:
            su_an = time.time()
            
            for g in self.gorev_listesi:
                if not self.is_running: break
                
                # Periyot kontrolü
                if su_an - g["son_tiklama"] >= g["sure"]:
                    tıklama_noktası = None
                    
                    # MOD 1: GÖRSEL ANALİZİ
                    if g["tur"] == "Görsel":
                        try:
                            konum = pyautogui.locateOnScreen(g["hedef"], confidence=0.8)
                            if konum is not None:
                                tıklama_noktası = pyautogui.center(konum)
                                print(f"\n[Görsel] Hedef bulundu: {os.path.basename(g['hedef'])}")
                        except pyautogui.ImageNotFoundException:
                            pass
                    
                    # MOD 2: DOĞRUDAN KOORDİNAT
                    elif g["tur"] == "Koordinat":
                        x, y = map(int, g["hedef"].split(","))
                        tıklama_noktası = (x, y)
                        print(f"\n[Koordinat] Zamana bağlı tetiklenme: ({x}, {y})")

                    # EĞER TIKLAMA NOKTASI BELLİYSE SERİ MAKRO BAŞLAR (0.01 sn hatasız döngü)
                    if tıklama_noktası is not None and self.is_running:
                        hedef_adet = g["adet"]
                        gecikme = g["hiz"]
                        
                        for i in range(1, hedef_adet + 1):
                            if not self.is_running: break
                            pyautogui.click(tıklama_noktası)
                            print(f" -> Tıklandı ({i}/{hedef_adet})")
                            if gecikme > 0: time.sleep(gecikme)
                        
                        # Görev bitti, zamanı kilitle
                        g["son_tiklama"] = time.time()
            
            time.sleep(0.05)
        self.stop_clicking()

    def on_closing(self):
        self.is_running = False
        keyboard.unhook_all()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoclickerApp(root)
    root.mainloop()