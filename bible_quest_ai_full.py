"""
Bible Quest AI - Version complète
- Voix IA (pyttsx3) en français
- Sauvegarde du profil joueur (profiles.json)
- Génération automatique de questions (templates locales)
Fichier data questions: bible_questions_ai.json
Fichier profils: profiles.json
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import random, json, os, time
import threading

try:
    import pyttsx3
    tts_engine = pyttsx3.init()

    voices = tts_engine.getProperty("voices")
    fr_voice = None
    for v in voices:
        if "fr" in (v.languages[0].decode('utf-8') if isinstance(v.languages[0], bytes) else str(v.languages[0])).lower() or "french" in v.name.lower():
            fr_voice = v.id
            break
    if fr_voice:
        tts_engine.setProperty("voice", fr_voice)
    tts_engine.setProperty("rate", 170)
    def speak(text):
        # run in thread to avoid blocking UI
        def _s():
            try:
                tts_engine.say(text)
                tts_engine.runAndWait()
            except Exception:
                pass
        threading.Thread(target=_s, daemon=True).start()
except Exception:
    tts_engine = None
    def speak(text):
        # fallback no-op
        return

# --- Files ---
QUESTIONS_FILE = "bible_questions_ai.json"
PROFILES_FILE = "profiles.json"

# --- Default questions (if file absent) ---
DEFAULT_QUESTIONS = [
    {"question": "Qui a construit l'arche ?", "options": ["Moïse","Abraham","Noé","David"], "answer": "Noé", "difficulty":"Débutant", "topic":"Histoire"},
    {"question": "Combien d'apôtres Jésus avait-il ?", "options": ["7","10","12","14"], "answer":"12", "difficulty":"Débutant", "topic":"Vie de Jésus"},
    {"question": "Quel prophète a été avalé par un grand poisson ?", "options":["Jonas","Ésaïe","Élie","Daniel"], "answer":"Jonas", "difficulty":"Débutant","topic":"Prophétie"},
    {"question":"Quel roi est célèbre pour sa sagesse ?", "options":["Saül","David","Salomon","Josias"], "answer":"Salomon","difficulty":"Intermédiaire","topic":"Sagesse"},
    {"question":"Dans quel livre trouve-t-on la vision des ossements desséchés ?", "options":["Ézéchiel","Daniel","Jérémie","Osée"], "answer":"Ézéchiel","difficulty":"Expert","topic":"Prophétie"},
]

# ensure files exist
if not os.path.exists(QUESTIONS_FILE):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_QUESTIONS, f, ensure_ascii=False, indent=2)

if not os.path.exists(PROFILES_FILE):
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# load/save helpers
def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_questions(qs):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(qs, f, ensure_ascii=False, indent=2)

def load_profiles():
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profiles(p):
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

# --- Générateur local de questions (templates) ---
TEMPLATES = {
    "Histoire": [
        ("Qui a {action} ?", ["Moïse","Abraham","Noé","David"]),
        ("Quel personnage biblique est lié à {indice} ?", ["Moïse","Josué","Samuel","David"])
    ],
    "Prophétie": [
        ("Quel prophète est associé à {indice} ?", ["Ésaïe","Jérémie","Ézéchiel","Daniel"]),
    ],
    "Vie de Jésus": [
        ("Dans quel évangile trouve-t-on la parabole de {indice} ?", ["Matthieu","Marc","Luc","Jean"]),
    ],
    "Sagesse": [
        ("Quel livre contient principalement des conseils et proverbes ?", ["Proverbes","Psaumes","Ésaïe","Romains"]),
    ],
}

# small filler words by topic to create variations
FILLERS = {
    "Histoire": [{"action":"construit l'arche"},{"action":"ouvert la mer Rouge"},{"indice":"le désert"}],
    "Prophétie": [{"indice":"les ossements desséchés"},{"indice":"la vision nocturne"}],
    "Vie de Jésus": [{"indice":"le bon samaritain"},{"indice":"le semeur"}],
    "Sagesse": [{"indice":"la sagesse du roi"}],
}

def generate_question_local(topic="Histoire", difficulty="Intermédiaire"):
    """Crée une question simple à partir de templates locales.
       Retourne un dict question compatible."""
    templates = TEMPLATES.get(topic, None)
    fillers = FILLERS.get(topic, [{}])
    if not templates:
        # fallback: pick a random existing question and slight modification
        qs = load_questions()
        base = random.choice(qs)
        return {"question": base["question"], "options": base["options"], "answer": base["answer"], "difficulty": difficulty, "topic": base.get("topic","Général")}
    tpl = random.choice(templates)
    filler = random.choice(fillers)
    try:
        q_text = tpl[0].format(**filler)
    except Exception:
        q_text = tpl[0]
    opts = list(tpl[1])
    random.shuffle(opts)
    correct = opts[0]
    return {"question": q_text, "options": opts, "answer": correct, "difficulty": difficulty, "topic": topic}

# --- Application principale ---
class BibleQuestAI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bible Quest AI")
        self.root.geometry("900x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#0b0f19")

        self.questions = load_questions()
        self.profiles = load_profiles()
        self.player = None
        self.level = "Débutant"
        self.performance = 0.5
        self.score = 0
        self.current = None
        self.selected = tk.StringVar()

        self.create_welcome()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    # --- Welcome / profil ---
    def create_welcome(self):
        self.clear()
        tk.Label(self.root, text="🧠 Bible Quest AI", font=("Orbitron", 36, "bold"), fg="#00eaff", bg="#0b0f19").pack(pady=20)
        name_btn = tk.Button(self.root, text="Profil", font=("Segoe UI", 12), bg="#00eaff", fg="#0b0f19", command=self.show_profiles)
        name_btn.place(x = 2, y = 2)
        tk.Button(self.root, text="connexion", font=("Segoe UI", 12), bg="#00cc88", fg="#0b0f19", command=self.login).place(x =55, y = 2)

        # Bouton de connexion additionnel
        tk.Label(self.root, text="Lancer L'entrainement", font=50, bg="#0b0f19", fg="white").place(x = 245 , y = 150 )
        tk.Label(self.root, text="Nouvelle Question", fg="white", font=30, bg="#0b0f19").place(x = 450 , y = 150)
        tk.Button(self.root, text="Ajouter", font=("Segoe UI", 14), bg="#ffaa00", width=12, command=self.test_generate).place(x = 450, y = 180)
        tk.Button(self.root, text="Commancer", font=("Segoe UI", 14), width=15, bg="#00eaff", fg="#0b0f19", command=self.start_quiz).place(x = 245, y = 180)
        tk.Label(self.root, text="Options  :", font=(("areal sens serif"), 14), fg="white", bg="#0b0f19").place(x = 10, y = 280 )
        tk.Label(self.root, text="importer des questios depuis un fichier json ", background="#0b0f19", fg="white", font=50, bd=2).place(x = 100, y = 280)
        tk.Button(self.root, text="Importer", font=12, bg="#ffaa00", width=12, command=self.import_questions).place(x = 100, y = 320 )

    def ask_player(self):
        name = simpledialog.askstring("Nom du joueur", "Ton nom (sera utilisé pour sauvegarder ta progression) :")
        if not name:
            return
        self.player = name.strip()
        if self.player in self.profiles:
            # restore
            p = self.profiles[self.player]
            self.performance = p.get("performance", 0.5)
            self.level = p.get("level", "Débutant")
            messagebox.showinfo("Profil chargé", f"Bienvenue {self.player} — niveau restauré : {self.level}")
        else:
            # new profile
            self.profiles[self.player] = {"performance": self.performance, "level": self.level, "history": [], "created": time.time()}
            save_profiles(self.profiles)
            messagebox.showinfo("Profil créé", f"Profil créé pour {self.player}")
        speak(f"Bienvenue {self.player}. Préparons votre entraînement biblique.")

    # --- import helper ---
    def import_questions(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Importer JSON", filetypes=[("JSON files","*.json"),("All files","*.*")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                new = json.load(f)
            if isinstance(new, list):
                self.questions.extend(new)
                save_questions(self.questions)
                messagebox.showinfo("Importé", f"{len(new)} questions importées.")
            else:
                messagebox.showerror("Erreur", "Le fichier doit contenir une liste JSON de questions.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'importer : {e}")

    def show_profiles(self):
        top = tk.Toplevel(self.root)
        top.title("Profils sauvegardés")
        top.geometry("500x400")
        frame = tk.Frame(top, padx=10, pady=10)
        frame.pack(fill="both", expand=True)
        # Ajout d'un bouton pour revenir / fermer la fenêtre
        tk.Button(frame, text="Retour", bg="#444", fg="white", command=top.destroy).pack(anchor="nw")
        for name, data in self.profiles.items():
            txt = f"{name} — niveau: {data.get('level','-')} — perf: {int(data.get('performance',0.5)*100)}% — cré: {time.strftime('%Y-%m-%d', time.localtime(data.get('created',0)))}"
            btn = tk.Button(frame, text=txt, anchor="w", command=lambda n=name: self.load_profile(n))
            btn.pack(fill="x", pady=4)

    def load_profile(self, name):
        self.player = name
        p = self.profiles[name]
        self.performance = p.get("performance",0.5)
        self.level = p.get("level","Débutant")
        messagebox.showinfo("Profil chargé", f"Profil {name} chargé.")
        speak(f"Profil {name} chargé.")

    # --- generate test ---
    def test_generate(self):
        q = generate_question_local(topic=random.choice(list(TEMPLATES.keys())), difficulty=random.choice(["Débutant","Intermédiaire","Expert"]))
        messagebox.showinfo("Question générée", f"{q['question']}\nRéponse attendue : {q['answer']}")
        # add to pool (ask user)
        if messagebox.askyesno("Ajouter ?", "Souhaites-tu ajouter cette question à la base ?"):
            self.questions.append(q)
            save_questions(self.questions)
            messagebox.showinfo("Ajouté", "Question ajoutée au fichier de questions.")

    # --- Start quiz / AI prompts ---
    def start_quiz(self):
        if not self.player:
            if messagebox.askyesno("Profil manquant", "Tu n'as pas chargé de profil. Créer un profil maintenant ?"):
                self.ask_player()
            else:
                return
        self.score = 0
        self.clear()
        # petit message IA
        prompt = random.choice([
            "Analyse de ta progression… ",
            "Calcul de la prochaine question… ",
            "Connexion à la base de la sagesse divine… ✨"
        ])
        label = tk.Label(self.root, text=prompt, font=("Segoe UI", 16), fg="#00eaff", bg="#0b0f19")
        label.pack(pady=50)
        speak(prompt)
        self.root.update()
        self.root.after(900, lambda: (label.destroy(), self.next_question()))

    # --- Choisir question adaptative (possibilité de génération si poche) ---
    def choose_question(self):
        # determine difficulty index from performance
        idx = min(2, max(0, int(self.performance * 3)))  # 0..3
        diffs = ["Débutant","Intermédiaire","Expert","Expert"]
        diff = diffs[idx]
        pool = [q for q in self.questions if q.get("difficulty","Débutant")==diff]
        # si pool trop petit, génère une nouvelle question localement
        if len(pool) < 2:
            # choose random topic
            topic = random.choice(list(TEMPLATES.keys()))
            newq = generate_question_local(topic=topic, difficulty=diff)
            self.questions.append(newq)
            save_questions(self.questions)
            pool.append(newq)
        return random.choice(pool)

    def next_question(self):
        self.clear()
        q = self.choose_question()
        self.current = q
        # header
        header = tk.Label(self.root, text=f"[{q.get('difficulty','-')}]  {q.get('topic','Général')}", fg="#ffaa00", bg="#0b0f19", font=("Segoe UI", 12))
        header.pack(pady=(20,6))
        q_label = tk.Label(self.root, text=q["question"], font=("Segoe UI", 20, "bold"), fg="#00eaff", bg="#0b0f19", wraplength=820)
        q_label.pack(pady=10)
        # TTS read
        speak("Question : " + q["question"])

        self.selected.set(None)
        for opt in q["options"]:
            rb = tk.Radiobutton(self.root, text=opt, variable=self.selected, value=opt,
                                font=("Segoe UI", 14), fg="white", bg="#0b0f19", selectcolor="#00eaff", anchor="w", justify="left")
            rb.pack(fill="x", padx=120, pady=4)

        tk.Button(self.root, text="Valider", bg="#00eaff", fg="#0b0f19", font=("Segoe UI", 14, "bold"), command=self.check_answer).pack(pady=18)
        # bottom info
        info = tk.Label(self.root, text=f"Joueur: {self.player} | Niveau IA estimé: {self.level} | Perf: {int(self.performance*100)}% | Score: {self.score}", fg="gray", bg="#0b0f19")
        info.pack(side="bottom", pady=8)

    def check_answer(self):
        if not self.selected.get():
            messagebox.showwarning("Réponse requise", "Choisis une réponse avant de valider.")
            return
        correct = self.current["answer"]
        if self.selected.get() == correct:
            self.score += 1
            self.performance = min(1.0, self.performance + 0.08)
            msg = "Bonne réponse ! Ta progression augmente."
            speak("Bonne réponse. Bravo.")
        else:
            self.performance = max(0.0, self.performance - 0.08)
            msg = f"Mauvaise réponse. La bonne réponse était : {correct}"
            speak("Mauvaise réponse. Ne t'inquiète pas, on réessaiera.")
        messagebox.showinfo("Résultat", msg)
        # save to profile history
        p = self.profiles.get(self.player, {"history":[]})
        hist = p.get("history", [])
        hist.append({"question": self.current["question"], "given": self.selected.get(), "correct": correct, "time": time.time()})
        p["history"] = hist[-200:]  # keep last 200
        p["performance"] = self.performance
        p["level"] = self.level
        self.profiles[self.player] = p
        save_profiles(self.profiles)
        # decide next step
        # small "IA" comment before next question
        prompt = "Préparation de la question suivante…"
        label = tk.Label(self.root, text=prompt, font=("Segoe UI", 14), fg="#00eaff", bg="#0b0f19")
        label.pack(pady=12)
        speak(prompt)
        self.root.update()
        self.root.after(700, lambda: (label.destroy(), self.next_question()))

    def back_to_menu(self):
        """Retourne à l'écran d'accueil principal."""
        self.create_welcome()

    def login(self):
        """Alias explicite pour la connexion (ouvre la saisie de nom/profil)."""
        # réutilise l'UI existante pour saisir ou charger un profil
        self.ask_player()

    def add_back_button(self, parent=None, pack_args=None):
        """Ajoute un bouton 'Retour au menu' dans la fenêtre courante.
           parent: widget où placer le bouton (par défaut self.root)
           pack_args: dict optionnel pour pack()"""
        if parent is None:
            parent = self.root
        if pack_args is None:
            pack_args = {"side": "top", "anchor": "nw", "padx": 10, "pady": 6}
        btn = tk.Button(parent, text="← Retour au menu", bg="#444", fg="white", command=self.back_to_menu)
        btn.pack(**pack_args)
        return btn

# --- MAIN ---
if __name__ == "__main__":
    root = tk.Tk()
    app = BibleQuestAI(root)
    root.mainloop()
